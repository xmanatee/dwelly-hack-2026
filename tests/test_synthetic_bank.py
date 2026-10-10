import json
import sqlite3
from datetime import UTC, datetime
from pathlib import Path

import pytest

from dwelly_bot.adapters.synthetic_banking.prepare import prepare
from dwelly_bot.adapters.synthetic_banking.sources import BankSource, bank_sources
from dwelly_bot.channels.intake import IdentityHints
from dwelly_bot.cli import main
from dwelly_bot.context.collector import ContextQuery
from dwelly_bot.local_cli import local_event
from dwelly_bot.storage import file_hash


@pytest.fixture
def bank(tmp_path: Path) -> Path:
    original = tmp_path / "original"
    original.mkdir()
    attachment = original / "cases/Banking & Financial Services/0001/attachments/receipt.txt"
    attachment.parent.mkdir(parents=True)
    attachment.write_text("Visible upload receipt; not proof of payment.")
    with sqlite3.connect(original / "banking_synth.sqlite") as db:
        db.executescript("""
        CREATE TABLE banks(bank_id, name);
        CREATE TABLE systems(system_id, description);
        CREATE TABLE customers(customer_id, name, status);
        CREATE TABLE cases(case_key, case_number, bank_id, outcome);
        CREATE TABLE case_labels(case_key, expected_path);
        CREATE TABLE case_events(case_key, seq, at, channel, sender, recipient, body,
            authenticated, actor_kind, is_decision_visible);
        CREATE TABLE case_system_responses(case_key, system_id, query_hint, response_text,
            fields_available, fields_absent);
        CREATE TABLE case_attachments(case_key,filename,first_event_seq,media_type,sha256);
        INSERT INTO banks VALUES('HV', 'Fictional Bank');
        INSERT INTO systems VALUES('transfer_journal','Outgoing transfers');
        INSERT INTO systems VALUES('card_system','Card records');
        INSERT INTO systems VALUES('complaints_team','Complaints');
        INSERT INTO customers VALUES('CUS-1','FINAL_NAME_SECRET','FINAL_STATE_SECRET');
        """)
        for n in (1, 2):
            key = f"SYN-{n:04d}"
            db.execute(
                "INSERT INTO cases VALUES(?,?,?,?)", (key, f"{n:04d}", "HV", "OUTCOME_SECRET")
            )
            db.execute("INSERT INTO case_labels VALUES(?,?)", (key, "LABEL_SECRET"))
            db.executemany(
                "INSERT INTO case_events VALUES(?,?,?,?,?,?,?,?,?,?)",
                [
                    (
                        key,
                        1,
                        "2026-01-01 09:00:00",
                        "Secure chat",
                        "Alex One" if n == 1 else "Foreign Person",
                        "Bank",
                        "Where is my transfer?",
                        1,
                        "customer",
                        1,
                    ),
                    (
                        key,
                        2,
                        "2026-01-01 10:00:00",
                        "Internal note",
                        "Bank",
                        "Team",
                        "FUTURE_SECRET",
                        None,
                        "bank_agent",
                        0,
                    ),
                ],
            )
            db.execute(
                "INSERT INTO case_system_responses VALUES(?,?,?,?,?,?)",
                (
                    key,
                    "transfer_journal",
                    "status of the specific transfer",
                    "Awaiting authorization" if n == 1 else "FOREIGN_SECRET",
                    '["status"]',
                    '["recipient credit"]',
                ),
            )
        db.executemany(
            "INSERT INTO case_attachments VALUES(?,?,?,?,?)",
            [
                ("SYN-0001", "receipt.txt", 1, "text/plain", file_hash(attachment)),
                ("SYN-0001", "FUTURE_SECRET.txt", 2, "text/plain", "not-visible"),
            ],
        )
        db.executemany(
            "INSERT INTO case_system_responses VALUES(?,?,?,?,?,?)",
            [
                ("SYN-0001", "card_system", "block card", "UNEXECUTED_CARD_BLOCK", "[]", "[]"),
                (
                    "SYN-0001",
                    "complaints_team",
                    "register complaint",
                    "UNEXECUTED_COMPLAINT",
                    "[]",
                    "[]",
                ),
            ],
        )
    dataset = tmp_path / "dataset"
    prepare(original, dataset)
    return dataset


def test_split_physically_removes_answers_final_state_and_later_events(bank: Path) -> None:
    with sqlite3.connect(bank / "state/decision.sqlite") as db:
        tables = {r[0] for r in db.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        assert not tables.intersection({"case_labels", "cases", "customers"})
        dump = "\n".join(db.iterdump())
        assert not any(
            secret in dump
            for secret in ("FINAL_STATE_SECRET", "FUTURE_SECRET", "OUTCOME_SECRET", "LABEL_SECRET")
        )
        assert db.execute("SELECT COUNT(*) FROM documents").fetchone()[0] == 1
        assert "UNEXECUTED" not in dump
    with sqlite3.connect(bank / "state/end-state.sqlite") as db:
        assert db.execute("SELECT status FROM customers").fetchone()[0] == "FINAL_STATE_SECRET"
        assert not db.execute("SELECT name FROM sqlite_master WHERE name LIKE 'case%'").fetchall()
    assert (bank / "evaluation/original/banking_synth.sqlite").exists()
    event = local_event(bank, "SYN-0001")
    assert event.hints.name == "Alex One"
    assert "LABEL_SECRET" not in event.text
    with pytest.raises(FileExistsError):
        prepare(bank / "evaluation/original", bank)


async def test_sources_resolve_alias_and_keep_scope_time_and_missing_fields(bank: Path) -> None:
    event = local_event(bank, "SYN-0001", "call")
    assert event.channel == "call"
    query = ContextQuery(
        scope_id=event.scope_id,
        as_of=event.received_at,
        hints=IdentityHints(phone=event.caller),
        question="Where is my transfer?",
    )
    sources = {s.name: s for s in bank_sources(bank)}
    identity = await sources["contact_directory"].lookup(query)
    assert len(identity.records) == 1 and "Alex One" in identity.records[0].text
    assert '"identity_verified": false' in identity.records[0].text
    response = await sources["bank_transfer_journal"].lookup(query)
    assert "recipient credit" in response.records[0].text
    assert "FOREIGN_SECRET" not in str(response)
    earlier = query.model_copy(update={"as_of": datetime(2025, 1, 1, tzinfo=UTC)})
    assert not (await sources["bank_transfer_journal"].lookup(earlier)).records
    wrong_phone = query.model_copy(update={"hints": IdentityHints(phone="+999wrong")})
    assert not (await sources["contact_directory"].lookup(wrong_phone)).records


async def test_ambiguous_names_remain_separate(bank: Path) -> None:
    with sqlite3.connect(bank / "state/decision.sqlite") as db:
        db.execute(
            "INSERT INTO contacts VALUES(?,?,?,?,?,?)",
            ("SYN-0001", "other", "Alex One", "other@example.invalid", "+999other", "third_party"),
        )
    result = await BankSource(
        bank / "state/decision.sqlite", "contact_directory", "Directory"
    ).lookup(
        ContextQuery(
            scope_id="SYN-0001",
            as_of=datetime(2026, 1, 1, 9, tzinfo=UTC),
            hints=IdentityHints(name="Alex One"),
        )
    )
    assert len(result.records) == 2 and any("Ambiguous" in w for w in result.warnings)


@pytest.mark.parametrize(
    ("channel", "operation"),
    [
        ("ticket", "ticket_comment"),
        ("email", "email_reply"),
        ("call", "speak_in_call"),
    ],
)
def test_local_runner_uses_product_pipeline_and_replays(
    bank: Path, tmp_path: Path, channel: str, operation: str
) -> None:
    args = [
        "local",
        "run",
        "--dataset",
        str(bank),
        "--case",
        "SYN-0001",
        "--channel",
        channel,
        "--state",
        str(tmp_path / "receipts.sqlite"),
    ]
    for name in ("first", "replay"):
        output = tmp_path / name
        assert main([*args, "--output", str(output)]) == 0
        text = (output / "context.md").read_text()
        assert "Awaiting authorization" in text and "Visible upload receipt" in text
        assert (
            "FOREIGN_SECRET" not in text
            and "FUTURE_SECRET" not in text
            and "LABEL_SECRET" not in text
        )
        result = json.loads((output / "result.json").read_text())
        assert result["receipts"][-1]["operation"] == operation
        assert all(r["replayed"] == (name == "replay") for r in result["receipts"])
        assert (output / "dataset.json").exists()


async def test_context_agent_reads_bank_tools_and_returns_observed_records(
    bank: Path, tmp_path: Path
) -> None:
    from pydantic_ai.messages import ModelMessage, ModelResponse, ToolCallPart
    from pydantic_ai.models.function import AgentInfo, FunctionModel

    from dwelly_bot.budget import BudgetLedger
    from dwelly_bot.channels.intake import normalize
    from dwelly_bot.context.collector import ContextCollector
    from dwelly_bot.context.investigator import AgentInvestigator
    from dwelly_bot.experiments.journal import Journal
    from dwelly_bot.models import BudgetedModel

    calls = 0

    def respond(messages: list[ModelMessage], info: AgentInfo) -> ModelResponse:
        nonlocal calls
        calls += 1
        if calls == 1:
            return ModelResponse(
                parts=[
                    ToolCallPart("read_source", {"source": s, "question": q})
                    for s, q in [
                        ("contact_directory", "Alex One"),
                        ("case_history", "request history"),
                        ("bank_transfer_journal", "transfer status and recipient credit"),
                    ]
                ]
            )
        assert "Awaiting authorization" in str(messages)
        assert "FOREIGN_SECRET" not in str(messages) and "LABEL_SECRET" not in str(messages)
        return ModelResponse(
            parts=[
                ToolCallPart(
                    info.output_tools[0].name,
                    {
                        "needs": ["Transfer status"],
                        "gaps": ["HALLUCINATED CLAIM FROM MODEL"],
                    },
                )
            ]
        )

    model = BudgetedModel(FunctionModel(respond), BudgetLedger(tmp_path / "budget.json"), "test")
    journal = Journal(tmp_path / "events.jsonl")
    try:
        context = await ContextCollector(
            bank_sources(bank), investigator=AgentInvestigator(model)
        ).collect(normalize(local_event(bank, "SYN-0001")), capabilities="handoff", journal=journal)
    finally:
        journal.close()
    assert "bank_transfer_journal: transfer status and recipient credit" in context.needs
    assert "Awaiting authorization" in context.text
    assert "HALLUCINATED CLAIM FROM MODEL" not in context.text
    assert "HALLUCINATED CLAIM FROM MODEL" in (tmp_path / "events.jsonl").read_text()
    assert calls == 2


def test_prepare_preserves_aware_instants_and_cleans_failed_projection(
    bank: Path, tmp_path: Path
) -> None:
    from dwelly_bot.adapters.synthetic_banking.prepare import timestamp

    assert timestamp("2026-01-01T10:00:00+02:00") == "2026-01-01T08:00:00+00:00"
    assert timestamp("2026-01-01 10:00:00") == "2026-01-01T10:00:00+00:00"
    original = bank / "evaluation/original"
    with pytest.raises(ValueError, match="outside"):
        prepare(original, original / "recursive-output")
    with sqlite3.connect(original / "banking_synth.sqlite") as db:
        db.execute("UPDATE cases SET case_key='../escape' WHERE case_key='SYN-0001'")
    output = tmp_path / "failed"
    with pytest.raises(ValueError, match="case ID"):
        prepare(original, output)
    assert not output.exists()
    assert not list(tmp_path.glob(".bank-prepare-*"))
    assert not (tmp_path / "escape.json").exists()


def test_cli_rejects_changed_case_bytes(bank: Path, capsys: pytest.CaptureFixture[str]) -> None:
    case = bank / "cases/SYN-0001.json"
    case.write_text(case.read_text() + "\n")
    with pytest.raises(SystemExit) as failure:
        main(["local", "list", "--dataset", str(bank)])
    assert failure.value.code == 2
    assert "case hash mismatch" in capsys.readouterr().err


@pytest.mark.parametrize("manifest", [[], {}, {"format": "bad"}])
def test_cli_reports_invalid_manifest_without_key_errors(bank: Path, manifest: object) -> None:
    (bank / "manifest.json").write_text(json.dumps(manifest))
    with pytest.raises(SystemExit) as failure:
        main(["local", "list", "--dataset", str(bank)])
    assert failure.value.code == 2


def test_replay_rejects_ambiguous_route_and_mismatched_scope(bank: Path) -> None:
    with sqlite3.connect(bank / "state/decision.sqlite") as db:
        db.execute(
            "INSERT INTO contacts SELECT scope_id, 'second', name, email, phone, actor_kind FROM contacts WHERE scope_id='SYN-0001'"
        )
    with pytest.raises(ValueError, match="exactly one"):
        local_event(bank, "SYN-0001", "call")
    path = bank / "cases/SYN-0001.json"
    data = json.loads(path.read_text())
    data["scope_id"] = "SYN-0002"
    path.write_text(json.dumps(data))
    with pytest.raises(ValueError, match="scope disagree"):
        local_event(bank, "SYN-0001")


async def test_local_failure_keeps_dataset_receipt_and_rejects_nested_state(
    bank: Path, tmp_path: Path
) -> None:
    from dwelly_bot.harness.local import run_local_pipeline
    from dwelly_bot.planning import Plan

    class BrokenPlanner:
        async def plan(self, context: str) -> Plan:
            raise ValueError("planner failure")

    manifest = json.loads((bank / "manifest.json").read_text())
    event = local_event(bank, "SYN-0001")
    output = tmp_path / "failed-run"
    with pytest.raises(ValueError, match="outside"):
        await run_local_pipeline(
            event,
            bank_sources(bank),
            BrokenPlanner(),
            output,
            state=output / "receipts.sqlite",
            dataset=manifest,
        )
    assert not output.exists()
    with pytest.raises(ValueError, match="planner failure"):
        await run_local_pipeline(
            event, bank_sources(bank), BrokenPlanner(), output, dataset=manifest
        )
    assert json.loads((output / "dataset.json").read_text()) == manifest
    assert (output / "failure.json").exists() and (output / "context.md").exists()
