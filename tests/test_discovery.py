"""Discovery contracts: grounding, source genre, trace-safe batching and honest unknowns."""

import json
from pathlib import Path
from typing import Any

import pytest
from pydantic_ai.messages import ModelResponse, ToolCallPart
from pydantic_ai.models.function import AgentInfo, FunctionModel

from dwelly_bot.analysis import AnalysisContext
from dwelly_bot.analysis.discovery import DiscoveryConfig, discover, select_review
from dwelly_bot.analysis.discovery_inputs import saved_conversations
from dwelly_bot.analysis.discovery_types import DiscoveryRecord, ScreenedRecord
from dwelly_bot.analysis.semantic import semantic_groups
from dwelly_bot.budget import BudgetLedger
from dwelly_bot.models import BudgetedModel
from dwelly_bot.storage import save_json


def record(id: str, kind: str = "question") -> DiscoveryRecord:
    return DiscoveryRecord.model_validate(
        {
            "id": id,
            "title": id,
            "kind": kind,
            "sources": [{"id": id, "text": "How do I close an account?", "source": "public"}],
        }
    )


@pytest.mark.filterwarnings("error:invalid value encountered in divide:RuntimeWarning")
def test_identical_vectors_have_a_finite_neutral_projection() -> None:
    result = semantic_groups([record("A"), record("B")], [[1.0, 1.0], [1.0, 1.0]])
    assert all(row["projection_x"] == row["projection_y"] == 0 for row in result["assignments"])


def screened(id: str, *, bad_quote: bool = False) -> dict[str, Any]:
    return {
        "id": id,
        "summary": "Closure request",
        "domain": "accounts",
        "topic": "Account closure",
        "outcome": "not_available",
        "evidence": [
            {"source_id": id, "quote": "not in source" if bad_quote else "close an account"}
        ],
    }


def test_policy_rule_is_not_observed_vulnerable_customer() -> None:
    policy = record("P1", "policy")
    output = ScreenedRecord.model_validate(
        {
            **screened("P1"),
            "findings": [
                {
                    "category": "support_need",
                    "description": "Needs support",
                    "scope": "observed_case",
                    "priority": "review",
                    "evidence": [{"source_id": "P1", "quote": "close an account"}],
                    "next_check": "review",
                }
            ],
        }
    )
    with pytest.raises(ValueError, match="observed customer"):
        output.check(policy)
    output.findings[0].scope = "policy_rule"
    output.check(policy)
    with pytest.raises(ValueError, match="established policy"):
        output.check(record("P1", "question"))


def test_saved_conversation_does_not_load_private_prompts_or_gold(tmp_path: Path) -> None:
    file = tmp_path / "capture.json"
    file.write_text(
        json.dumps(
            {
                "runs": [
                    {
                        "id": "run",
                        "cases": [
                            {
                                "id": "one",
                                "model_messages": ["PRIVATE CUSTOMER INSTRUCTIONS"],
                                "verifier": {"expected": "GOLD"},
                                "state_snapshots": {
                                    "after": {
                                        "conversation": [
                                            {
                                                "role": "customer",
                                                "message": "Please help",
                                                "timestamp": "2026-10-09T10:00:00+01:00",
                                            },
                                            {"role": "assistant", "message": "What happened?"},
                                        ]
                                    }
                                },
                            }
                        ],
                    }
                ]
            }
        )
    )
    records = saved_conversations(file, domain="banking")
    assert records[0].domain == "banking"
    assert records[0].sources[0].speaker == "customer"
    assert records[0].sources[0].timestamp == "2026-10-09T10:00:00+01:00"
    assert records[0].sources[0].origin == "message"
    payload = json.dumps(records[0].model_dump())
    assert "PRIVATE" not in payload and "GOLD" not in payload


def test_saved_conversations_read_compressed_bundles(tmp_path: Path) -> None:
    file = tmp_path / "capture.json.gz"
    save_json(
        file,
        {
            "runs": [
                {
                    "id": "run",
                    "cases": [
                        {
                            "id": "case",
                            "state_snapshots": {
                                "after": {"conversation": [{"role": "customer", "message": "Hi"}]}
                            },
                        }
                    ],
                }
            ]
        },
    )
    assert saved_conversations(file)[0].sources[0].text == "Hi"


async def test_batch_keeps_valid_neighbors_and_repairs_only_bad_record(tmp_path: Path) -> None:
    pytest.importorskip("sklearn")
    calls: list[str] = []

    def response(messages: Any, info: AgentInfo) -> ModelResponse:
        payload = json.loads(
            next(
                part.content
                for message in reversed(messages)
                for part in message.parts
                if getattr(part, "part_kind", None) == "user-prompt"
            )
        )
        schema = info.output_tools[0].parameters_json_schema
        title = schema.get("title", "")
        calls.append(title)
        if "DiscoveryBatch" in title:
            output = {
                "records": [
                    screened(r["id"], bad_quote=r["id"] == "bad") for r in payload["records"]
                ]
            }
        elif title == "ScreenedRecord":
            output = screened(payload["record"]["id"])
        elif title == "TaxonomyDraft":
            labels = [p["alias_id"] for p in payload["candidate_labels"]]
            output = {
                "intents": [
                    {
                        "id": "accounts.close",
                        "parent": "accounts",
                        "name": "Close account",
                        "definition": "Closure checks",
                        "aliases": labels,
                        "inclusion": "Closure request",
                        "exclusion": "Other changes",
                        "representative_ids": ["good"],
                    }
                ]
            }
        elif title.startswith("AssignAliases"):
            output = {
                "assignments": [
                    {
                        "alias_id": row["alias_id"],
                        "intent_ids": ["accounts.close"],
                        "status": "matched",
                    }
                    for row in payload["aliases"]
                ]
            }
        elif title == "ConflictBatch":
            output = {"conflicts": []}
        elif title == "AuditBatch":
            output = {
                "records": [
                    {
                        "id": r["id"],
                        "decision": "supported",
                        "reason": "Source supports interpretation",
                        "evidence": [{"source_id": r["id"], "quote": "close an account"}],
                    }
                    for r in payload["records"]
                ]
            }
        else:
            raise AssertionError(title)
        return ModelResponse(
            parts=[ToolCallPart(info.output_tools[0].name, output)],
            provider_details={"cost": 0.001},
        )

    model = BudgetedModel(
        FunctionModel(response), BudgetLedger(tmp_path / "budget.json", 1), "fixture"
    )
    ctx = AnalysisContext(tmp_path, tmp_path / "run", tmp_path / "cache", model=model)
    result = await discover(
        ctx,
        [record("good"), record("bad")],
        DiscoveryConfig(batch_size=2, deep_sample=0, audit_sample=1, conflict_pairs=1),
    )
    assert result["screened_records"] == 2
    assert result["taxonomy"]["intents"][0]["id"] == "accounts.close"
    assert result["taxonomy"]["unmapped_aliases"] == []
    assert calls.count("ScreenedRecord") == 1
    assert result["screens"]["bad"]["evidence"][0]["quote"] == "close an account"
    batches = [json.loads(f.read_text()) for f in (ctx.output / "steps").glob("*.json")]
    assert any(
        d.get("output", {}).get("records", [])
        and any(
            row.get("evidence", [{}])[0].get("quote") == "not in source"
            for row in d["output"]["records"]
        )
        for d in batches
    )
    assert result["ground_truth_metrics"] is None
    assert model.ledger.summary()["request_count"] == len(calls)


def test_review_reasons_remain_separate_and_samples_unique() -> None:
    sources = [record("one"), record("two"), record("three")]
    screens = {id: ScreenedRecord.model_validate(screened(id)) for id in [r.id for r in sources]}
    geometry = {
        "clusters": [{"representatives": ["one"], "boundary_ids": ["two"]}],
        "assignments": [{"id": "three", "neighbor_distance": 0.9}],
    }
    selection = select_review(sources, screens, geometry, limit=3, seed=0)
    assert len({r["id"] for r in selection}) == 3
    reasons = {r["id"]: r["reasons"] for r in selection}
    assert "representative" in reasons["one"] and "cluster_boundary" in reasons["two"]
    assert "semantic_novelty" in reasons["three"]


@pytest.mark.parametrize("order", [[0, 1, 2], [2, 1, 0]])
def test_small_corpus_keeps_neighbors_without_forcing_density_groups(order: list[int]) -> None:
    pytest.importorskip("sklearn")
    records = [record("a"), record("b"), record("c")]
    vectors: list[list[float]] = [[1, 0], [0.9, 0.1], [0, 1]]
    result = semantic_groups([records[i] for i in order], [vectors[i] for i in order])
    assert result["clusters"] == []
    assert all(row["cluster"] == -1 for row in result["assignments"])
    assert [pair["ids"] for pair in result["pairs"]] == [["a", "b"], ["b", "c"]]


@pytest.mark.parametrize("kind", ["document", "question"])
def test_ordinary_sources_do_not_define_policy(kind: str) -> None:
    row = ScreenedRecord.model_validate(screened("A"))
    from dwelly_bot.analysis.discovery_types import Finding

    row.findings = [
        Finding(
            category="policy_gap",
            description="Check",
            scope="policy_rule",
            priority="review",
            evidence=row.evidence,
            next_check="Review source authority",
        )
    ]
    with pytest.raises(ValueError, match="established policy"):
        row.check(record("A", kind))


@pytest.mark.parametrize("status", ["matched", "uncertain", "invalid", "failed"])
async def test_taxonomy_keeps_uncertain_and_failed_assignments_unmapped(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, status: str
) -> None:
    from dwelly_bot.analysis.taxonomy import build_taxonomy

    async def ask(
        self: AnalysisContext,
        name: str,
        inputs: Any,
        schema: Any,
        instructions: str,
        **options: Any,
    ) -> Any:
        if name == "taxonomy-definitions":
            value = {
                "intents": [
                    {
                        "id": "accounts.close",
                        "name": "Close account",
                        "parent": "Accounts",
                        "definition": "Close an account",
                        "inclusion": "Closure",
                        "exclusion": "Opening",
                        "aliases": [inputs["candidate_labels"][0]["alias_id"]],
                        "representative_ids": ["A"],
                    }
                ]
            }
        else:
            if status == "failed":
                raise ValueError("assignment failed")
            value = {
                "assignments": [
                    {
                        "alias_id": row["alias_id"],
                        "intent_ids": ["accounts.close"],
                        "status": status,
                    }
                    for row in inputs["aliases"]
                ]
            }
        result = schema.model_validate(value)
        options["validate"](result)
        return result

    monkeypatch.setattr(AnalysisContext, "ask", ask)
    ctx = AnalysisContext(tmp_path, tmp_path / "run", tmp_path / "cache")
    result = await build_taxonomy(
        ctx, {"A": ScreenedRecord.model_validate(screened("A"))}, kinds=["question"]
    )
    assert result.intents[0].aliases == (["Account closure"] if status == "matched" else [])
    assert result.unmapped_aliases == ([] if status == "matched" else ["Account closure"])
    assert bool(result.assignment_errors) == (status in {"invalid", "failed"})


def test_conflict_citations_must_belong_to_named_records() -> None:
    from dwelly_bot.analysis.discovery_types import CrossConflict, ObservedPattern

    finding = CrossConflict.model_validate(
        {
            "record_ids": ["A", "B"],
            "description": "Conflicting instructions",
            "status": "potential_conflict",
            "evidence": [
                {"source_id": "A", "quote": "close an account"},
                {"source_id": "C", "quote": "close an account"},
            ],
            "next_check": "Review",
        }
    )
    with pytest.raises(ValueError, match="Citation"):
        finding.check([record("A"), record("B"), record("C")])
    finding.evidence[1].source_id = "B"
    finding.check([record("A"), record("B")])
    finding.record_ids = ["A"]
    finding.status = "internal_inconsistency"
    finding.evidence[1].source_id = "A"
    finding.evidence[1].quote = "How do I"
    finding.check([record("A")])
    pattern = ObservedPattern(
        intent_id="accounts.close",
        case_ids=["A", "B"],
        steps=[],
        negative_paths=[],
        unknown_checks=[],
        evidence=finding.evidence,
    )
    with pytest.raises(ValueError, match="Every pattern case"):
        pattern.check([record("A"), record("B")])
    pattern.evidence[1].source_id = "B"
    pattern.check([record("A"), record("B")])
    pattern.case_ids = ["A", "A"]
    with pytest.raises(ValueError, match="distinct supplied"):
        pattern.check([record("A")])


async def test_refinement_preserves_sources_and_drops_stale_procedures(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from dwelly_bot.analysis import refine
    from dwelly_bot.analysis.discovery_types import TaxonomyDraft
    from dwelly_bot.storage import save_json

    parent = tmp_path / "parent"
    result = {
        "eligible_records": 1,
        "screens": {"A": ScreenedRecord.model_validate(screened("A")).model_dump()},
        "taxonomy": {"intents": []},
        "review_sample": [],
        "deep_extractions": {},
        "conflicts": {"conflicts": []},
        "audits": {"records": []},
        "errors": [],
        "geometry": {"assignments": [], "clusters": [], "pairs": [], "embedding_model": "fixture"},
        "observed_patterns": {"patterns": [{"intent_id": "old.intent"}]},
        "procedure_drafts": [{"intent_id": "old.intent"}],
    }
    save_json(parent / "discovery.json", result)
    save_json(parent / "records.json", [record("A").model_dump()])
    original = (parent / "discovery.json").read_bytes()
    calls = 0

    async def taxonomy(ctx: AnalysisContext, screens: Any, *, kinds: list[str]) -> TaxonomyDraft:
        nonlocal calls
        calls += 1
        assert list(screens) == ["A"] and kinds == ["question"]
        return TaxonomyDraft(intents=[], unmapped_aliases=["Account closure"])

    monkeypatch.setattr(refine, "build_taxonomy", taxonomy)
    for index in range(2):
        ctx = AnalysisContext(parent, tmp_path / f"refined-{index}", tmp_path / "cache")
        report = await refine.build(ctx)
        updated = json.loads((ctx.output / "discovery.json").read_text())
        assert updated["observed_patterns"] == {"patterns": []}
        assert updated["procedure_drafts"] == []
        assert updated["taxonomy_dependents_status"] == "not_recomputed"
        assert report.title == "Refined operational discovery"
        assert "records.json" in ctx.sources
        parent = ctx.output
    assert calls == 2
    assert (tmp_path / "parent/discovery.json").read_bytes() == original
    (parent / "records.json").write_text("[]")
    with pytest.raises(ValueError, match="missing original"):
        await refine.build(AnalysisContext(parent, tmp_path / "broken", tmp_path / "cache"))
    assert calls == 2


async def test_refinement_requires_original_records(tmp_path: Path) -> None:
    from dwelly_bot.analysis.refine import build
    from dwelly_bot.storage import save_json

    source = tmp_path / "source"
    source.mkdir()
    save_json(source / "discovery.json", {})
    ctx = AnalysisContext(source, tmp_path / "out", tmp_path / "cache")
    with pytest.raises(FileNotFoundError, match=r"records\.json"):
        await build(ctx)
