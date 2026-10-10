"""Analysis contracts: source boundaries, cache reuse, truthful runs and offline reports."""

import asyncio
import json
from html.parser import HTMLParser
from pathlib import Path
from typing import Any

import pytest
from pydantic import ValidationError
from pydantic_ai.messages import ModelResponse, ToolCallPart
from pydantic_ai.models.function import AgentInfo, FunctionModel

from dwelly_bot.analysis import (
    AnalysisContext,
    Relationship,
    Report,
    Table,
    enrich,
    relationships,
)
from dwelly_bot.analysis.discovery_inputs import saved_conversations
from dwelly_bot.analysis.exploration import add_saved_run
from dwelly_bot.analysis.llm import extract
from dwelly_bot.analysis.recipes import numeric_summary, sample
from dwelly_bot.budget import BudgetLedger
from dwelly_bot.cache import JsonCache
from dwelly_bot.context.evidence import Citation, EvidenceText, ProcedureDraft, ProcedureStep
from dwelly_bot.models import BudgetedModel
from dwelly_bot.reporting import ReportProfile, render
from dwelly_bot.reporting.html import build
from dwelly_bot.storage import fingerprint, load_json, save_json


def test_relationships_refuse_ambiguous_join() -> None:
    children = Table("messages", [{"customer": "a"}, {"customer": "unknown"}])
    parents = Table("customers", [{"id": "a"}, {"id": "a"}])
    result = relationships(
        [children, parents], [Relationship("messages", "customer", "customers", "id")]
    )[0]
    assert result["duplicate_parent_keys"] == 1
    assert result["unmatched_children"] == 1
    with pytest.raises(ValueError, match="unique"):
        enrich(children, parents, "customer", "id", "customer_")
    unique = Table("customers", [{"id": "a", "segment": "one"}])
    joined = enrich(children, unique, "customer", "id", "customer_")
    assert len(joined.rows) == 2 and joined.rows[0]["customer_segment"] == "one"
    assert "customer_segment" not in joined.rows[1]
    with pytest.raises(ValueError, match="missing columns"):
        enrich(children, unique, "missing", "id", "x_")
    unique.role = "evaluation_only"
    with pytest.raises(ValueError, match="Evaluation-only"):
        enrich(children, unique, "customer", "id", "customer_")


def test_content_cache_reuses_and_invalidates_sources(tmp_path: Path) -> None:
    source = tmp_path / "data.txt"
    source.write_text("one")
    calls = 0

    def read() -> dict[str, str]:
        nonlocal calls
        calls += 1
        return {"text": source.read_text()}

    ctx = AnalysisContext(tmp_path, tmp_path / "run", tmp_path / "cache", code_hash="fixture")
    assert ctx.cached("read", {}, read, files=[source]) == {"text": "one"}
    assert ctx.cached("read", {}, read, files=[source]) == {"text": "one"}
    assert calls == 1 and ctx.steps[-1]["status"] == "cache_hit"
    source.write_text("two")
    assert ctx.cached("read", {}, read, files=[source]) == {"text": "two"}
    assert calls == 2
    with pytest.raises(ValueError, match="inside"):
        ctx.cached("outside", {}, read, files=[tmp_path.parent / "anything"])
    key = fingerprint("corruption-probe")
    ctx.cache.put(key, {"valid": True})
    (tmp_path / "cache" / (key + ".json.gz")).write_bytes(b"broken")
    with pytest.raises(OSError):
        ctx.cache.get(key)


def test_failed_transform_never_becomes_a_cached_success(tmp_path: Path) -> None:
    cache = JsonCache(tmp_path)
    key = fingerprint("failure")

    def failed() -> None:
        raise RuntimeError("real failure")

    with pytest.raises(RuntimeError):
        cache.compute(key, failed)
    assert cache.get(key) is None
    with pytest.raises(ValueError, match="JSON value"):
        cache.put(key, None)


def test_cited_model_extraction_reuses_paid_result_and_same_budget(tmp_path: Path) -> None:
    calls = 0
    sources = [EvidenceText(id="M1", text="Please close my account.", source="messages")]

    def response(_: Any, info: AgentInfo) -> ModelResponse:
        nonlocal calls
        calls += 1
        return ModelResponse(
            parts=[
                ToolCallPart(
                    info.output_tools[0].name,
                    {
                        "summary": "Account closure request",
                        "goals": [
                            {
                                "text": "Close account",
                                "support": "explicit",
                                "evidence": [{"source_id": "M1", "quote": "close my account"}],
                            }
                        ],
                    },
                )
            ],
            provider_details={"cost": 0.002},
        )

    ledger = BudgetLedger(tmp_path / "budget.json", 1)
    ledger.reserve_account(0.01, "other-role", "baseline")
    model = BudgetedModel(FunctionModel(response), ledger, "analysis")
    first = AnalysisContext(tmp_path, tmp_path / "one", tmp_path / "cache", model=model)
    second = AnalysisContext(
        tmp_path, tmp_path / "two", tmp_path / "cache", model=model, code_hash="changed-chart"
    )
    result = asyncio.run(extract(first, sources))
    repeated = asyncio.run(extract(second, sources))
    assert repeated == result and calls == 1
    assert ledger.summary()["request_count"] == 2
    assert second.steps[-1]["new_requests"] == 0
    assert second.last_model_trace and second.last_model_trace["reused"] is True
    assert list((second.output / "steps").glob("*.json"))
    with pytest.raises(ValueError, match="public"):
        asyncio.run(
            extract(
                first,
                [EvidenceText(id="gold", text="private", source="eval", role="evaluation_only")],
            )
        )
    assert calls == 1


def test_invalid_model_citation_is_preserved_but_not_cached(tmp_path: Path) -> None:
    def response(_: Any, info: AgentInfo) -> ModelResponse:
        return ModelResponse(
            parts=[
                ToolCallPart(
                    info.output_tools[0].name,
                    {
                        "summary": "Unsupported",
                        "facts": [
                            {
                                "text": "invented",
                                "support": "explicit",
                                "evidence": [{"source_id": "M1", "quote": "not in original"}],
                            }
                        ],
                    },
                )
            ]
        )

    ctx = AnalysisContext(
        tmp_path,
        tmp_path / "run",
        tmp_path / "cache",
        model=BudgetedModel(
            FunctionModel(response), BudgetLedger(tmp_path / "budget.json", 1), "bad"
        ),
    )
    with pytest.raises(ValueError, match="Citation"):
        asyncio.run(extract(ctx, [EvidenceText(id="M1", text="Original", source="messages")]))
    saved = json.loads(next((ctx.output / "steps").glob("*.json")).read_text())
    assert saved["output"]["facts"][0]["text"] == "invented"
    assert saved["status"] == "error" and saved["messages"]
    assert not list((tmp_path / "cache").glob("*.json.gz"))


def test_procedure_draft_cannot_approve_or_invent_tools() -> None:
    policy = EvidenceText(id="P1", text="Read identity before closing.", source="policy")
    draft = ProcedureDraft(
        intent="closure",
        required_information=["identity"],
        steps=[
            ProcedureStep(
                action="check identity",
                tool="invented",
                condition="always",
                evidence=[Citation(source_id="P1", quote="Read identity")],
            )
        ],
        stop_conditions=["identity unknown"],
        verified_outcome="closed state",
    )
    with pytest.raises(ValueError, match="unavailable"):
        draft.check_sources([policy], ["read_identity"])
    with pytest.raises(ValidationError):
        ProcedureDraft.model_validate({**draft.model_dump(), "status": "approved"})


@pytest.mark.parametrize(
    "status,expected", [("available", "pass"), ("error", "unknown"), ("unavailable", "unknown")]
)
@pytest.mark.parametrize("suffix", [".json", ".json.gz"])
def test_saved_overlay_requires_independent_verification(
    tmp_path: Path, status: str, expected: str, suffix: str
) -> None:
    from dwelly_bot.experiments.provenance import dataset_hash

    data = tmp_path / "dataset"
    data.mkdir()
    (data / "source.json").write_text('{"files": []}')
    corpus_hash = dataset_hash(data)
    source = tmp_path / ("captured" + suffix)
    save_json(
        source,
        {
            "schema_version": 1,
            "runs": [
                {
                    "id": "one",
                    "manifest": {
                        "assigned_case_ids": ["c1", "missing"],
                        "dataset_hash": corpus_hash,
                    },
                    "cases": [
                        {
                            "id": "c1",
                            "execution_status": "error",
                            "input": {"question": "Received request"},
                            "verifier": {"status": status, "goal_pass": True},
                            "answer": "saved",
                            "state_snapshots": {
                                "after": {
                                    "conversation": [
                                        {"role": "customer", "message": "Close my account"}
                                    ]
                                }
                            },
                            "tool_events": [{"tool": "read", "status": "returned"}],
                        }
                    ],
                }
            ],
        },
    )
    before = source.read_bytes()
    report = Report(title="saved")
    ctx = AnalysisContext(
        data, tmp_path / "run", tmp_path / "cache", parameters={"saved_run": str(source)}
    )
    add_saved_run(report, ctx)
    outcomes = next(block.data["rows"] for block in report.blocks if block.title == "Run outcomes")
    assert outcomes[0]["execution_errors"] == 2
    cases = next(block.data["rows"] for block in report.blocks if block.kind == "records")
    assert cases[0]["goal_status"] == expected
    assert source.read_bytes() == before
    assert ctx.steps == []
    original = load_json(source)
    report = build(
        original, ReportProfile(title="Custom report", fields={"Request": "/input/question"})
    )
    records = next(block.data["rows"] for block in report.blocks if block.kind == "records")
    assert report.title == "Custom report" and records[0]["fields"]["Request"] == "Received request"
    assert records[0]["goal_status"] == expected and records[1]["goal_status"] == "unknown"
    assert report.blocks[0].data["Assigned attempts"] == 2
    assert original == load_json(source)
    conversations = saved_conversations(source)
    assert len(conversations) == 1
    assert conversations[0].sources[0].text == "Close my account"
    with pytest.raises(ValidationError):
        ReportProfile(fields={"Verified outcome": "/answer"})


class PageParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.remote_scripts: list[str] = []
        self.inline_styles: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if "style" in dict(attrs):
            self.inline_styles.append(tag)
        if tag == "script" and dict(attrs).get("src"):
            self.remote_scripts.append(str(dict(attrs)["src"]))


def test_offline_report_escapes_sources_and_accepts_custom_plotly(tmp_path: Path) -> None:
    pytest.importorskip("plotly")
    from plotly.graph_objects import Bar, Figure

    hostile = '</script><img src="https://example.com" onerror="alert(1)">'
    report = Report(title="Probe")
    report.table("table", [{"text": hostile}])
    report.chart("chart", Figure(Bar(x=[hostile], y=[1])))
    output = tmp_path / "analysis.html"
    render(report, output)
    page = output.read_text()
    assert hostile not in page
    assert "connect-src 'none'" in page and "__REPORT_DATA__" not in page
    parser = PageParser()
    parser.feed(page)
    assert parser.remote_scripts == [] and parser.inline_styles == []
    assert report.blocks[0].data["rows"][0]["text"] == hostile
    evidence = tmp_path / "evidence.json"
    evidence.write_text('{"original":true}')
    with pytest.raises(ValueError, match="HTML reports require"):
        render(report, evidence)
    assert evidence.read_text() == '{"original":true}'


def test_sampling_and_numeric_quality_are_explicit() -> None:
    rows = [{"id": i} for i in range(30)]
    assert sample(rows, 5, 10) == sample(rows, 5, 10)
    assert len(sample(rows, 50)) == 30
    result = numeric_summary(Table("amounts", [{"x": 1}, {"x": 3}, {"x": "invalid"}]), "x")
    assert result["median"] == 2 and result["invalid_or_missing"] == 1


def test_thread_chronology_preserves_message_citations() -> None:
    from dwelly_bot.analysis.data import threads

    rows = [
        {
            "case": "C1",
            "id": "second",
            "at": "2026-10-09T10:01:00+00:00",
            "role": "customer",
            "body": "Correction",
        },
        {
            "case": "C1",
            "id": "first",
            "at": "2026-10-09T11:00:00+01:00",
            "role": "customer",
            "body": "Original",
        },
    ]
    result = threads(
        Table("messages", rows, role="historical"),
        case_id="case",
        message_id="id",
        text="body",
        timestamp="at",
        speaker="role",
    )
    assert result.rows[0]["sources"][0]["id"] == "C1/first"
    assert result.rows[0]["text"].index("Original") < result.rows[0]["text"].index("Correction")
    rows[0]["at"] = "2026-10-09T10:00:00"
    with pytest.raises(ValueError, match="timezone"):
        threads(
            Table("messages", rows),
            case_id="case",
            message_id="id",
            text="body",
            timestamp="at",
            speaker="role",
        )


def test_analysis_rejects_combined_exports_and_foreign_run(tmp_path: Path) -> None:
    from dwelly_bot.analysis.session import validate_analysis

    with pytest.raises(ValueError, match="exactly one dataset"):
        validate_analysis(Report(title="Mixed", receipt={"source_analyses": ["a", "b"]}))
    data = tmp_path / "dataset"
    data.mkdir()
    (data / "source.json").write_text('{"files": []}')
    saved = tmp_path / "run.json"
    row = {
        "id": "a",
        "manifest": {"assigned_case_ids": ["c"], "dataset_hash": "foreign"},
        "cases": [],
    }
    saved.write_text(json.dumps({"schema_version": 1, "runs": [row]}))
    ctx = AnalysisContext(
        data, tmp_path / "analysis", tmp_path / "cache", parameters={"saved_run": str(saved)}
    )
    with pytest.raises(ValueError, match="same pinned dataset"):
        ctx.saved_run()
    saved.write_text(json.dumps({"schema_version": 1, "runs": [row, {**row, "id": "b"}]}))
    with pytest.raises(ValueError, match="one saved run"):
        ctx.saved_run()
