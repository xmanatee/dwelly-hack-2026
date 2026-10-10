"""Regrading uses only captured results and independent evaluator state."""

from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any

import pytest
from pydantic_evals.reporting import EvaluationReportAdapter

from dwelly_bot.contracts import AgentCase, RunConfig, Verification
from dwelly_bot.evaluation.saved import grade_bundle
from dwelly_bot.experiments.provenance import dataset_hash
from dwelly_bot.storage import fingerprint


def _bundle(rows: list[dict[str, Any]], assigned: list[str] | None = None) -> dict[str, Any]:
    return {
        "schema_version": 1,
        "runs": [
            {
                "id": "saved-run",
                "manifest": {
                    "assigned_case_ids": assigned or [row["id"] for row in rows],
                },
                "cases": rows,
            }
        ],
    }


class SavedSession:
    def __init__(self, adapter: SavedAdapter, case: AgentCase):
        self.adapter = adapter
        self.case = case

    async def run(self, runtime: Any) -> Any:
        pytest.fail("A saved-artifact grader must never run a subject or model")

    def snapshot(self) -> dict[str, Any]:
        pytest.fail("A saved-artifact grader must not re-capture or replay subject state")

    def grade(self, execution: dict[str, Any]) -> dict[str, Any]:
        assert "verifier" not in execution
        assert "metadata" not in execution
        assert "score" not in execution
        self.adapter.graded.append(copy.deepcopy(execution))
        if self.case.id == "unknown":
            return {"status": "available", "goal_pass": None, "checks": []}
        if self.case.id == "error":
            raise ValueError("Deliberate local verifier failure")
        passed = execution.get("answer") == "correct"
        return {
            "status": "available",
            "goal_pass": passed,
            "checks": [
                {
                    "id": "exact_answer",
                    "status": "pass" if passed else "fail",
                    "actual": execution.get("answer"),
                    "expected": "correct",
                }
            ],
        }


class SavedAdapter:
    name = "offline-reference"

    def __init__(self) -> None:
        self.graded: list[dict[str, Any]] = []
        self.prepared: list[str] = []

    def load_cases(self, root: Path, ids: list[str] | None = None) -> list[AgentCase]:
        return [
            AgentCase(id=value, dataset=self.name, title=value, input={"task": value})
            for value in ("pass", "fail", "unknown", "error")
        ]

    def prepare(self, case: AgentCase, root: Path, config: RunConfig) -> SavedSession:
        self.prepared.append(case.id)
        return SavedSession(self, case)

    def grade_saved(
        self, case: AgentCase, root: Path, config: RunConfig, execution: dict[str, Any]
    ) -> dict[str, Any]:
        return self.prepare(case, root, config).grade(execution)


@pytest.mark.parametrize("invalid", ["missing_input", "modified_hash"])
async def test_production_capture_requires_original_input_and_fingerprint(
    tmp_path: Path, invalid: str
) -> None:
    (tmp_path / "source.json").write_text('{"files":[]}')
    row: dict[str, Any] = {
        "id": "pass",
        "answer": "correct",
        "execution_status": "completed",
        "input": {"task": "pass"},
        "input_hash": fingerprint({"task": "pass"}),
    }
    if invalid == "missing_input":
        row.pop("input")
    else:
        row["input_hash"] = "modified"
    bundle = _bundle([row])
    bundle["runs"][0]["manifest"]["dataset_hash"] = dataset_hash(tmp_path)
    adapter = SavedAdapter()
    graded, _ = await grade_bundle(bundle, tmp_path, adapter, RunConfig())  # type: ignore[arg-type]
    assert graded["runs"][0]["cases"][0]["verifier"]["goal_pass"] is None
    assert not adapter.prepared


async def test_saved_run_cannot_be_regraded_against_different_corpus(tmp_path: Path) -> None:
    (tmp_path / "source.json").write_text('{"files":[]}')
    bundle = _bundle([{"id": "pass", "answer": "correct"}])
    bundle["runs"][0]["manifest"]["dataset_hash"] = "another corpus"
    with pytest.raises(ValueError, match="dataset fingerprint"):
        await grade_bundle(bundle, tmp_path, SavedAdapter(), RunConfig())  # type: ignore[arg-type]


@pytest.mark.asyncio
async def test_saved_verification_distinguishes_pass_failure_unknown_and_missing(
    tmp_path: Path,
) -> None:
    adapter = SavedAdapter()
    rows: list[dict[str, Any]] = [
        {"id": "pass", "answer": "correct", "execution_status": "completed"},
        {
            "id": "fail",
            "answer": "wrong",
            "execution_status": "completed",
            "verifier": {"status": "available", "goal_pass": True},
            "metadata": {"grade": "pass"},
            "score": 1,
        },
        {"id": "unknown", "answer": "unknown", "execution_status": "completed"},
        {"id": "error", "answer": "correct", "execution_status": "completed"},
    ]
    original = _bundle(rows, ["pass", "fail", "unknown", "error", "missing"])
    before = copy.deepcopy(original)
    graded, report = await grade_bundle(original, tmp_path, adapter, RunConfig())  # type: ignore[arg-type]
    result = {row["id"]: row for row in graded["runs"][0]["cases"]}
    assert original == before
    assert result["pass"]["verifier"]["goal_pass"] is True
    assert result["fail"]["verifier"]["goal_pass"] is False
    assert result["unknown"]["verifier"]["goal_pass"] is None
    assert result["error"]["verifier"]["goal_pass"] is None
    assert result["error"]["verifier"]["status"] == "error"
    assert result["missing"]["execution_status"] == "missing_result"
    assert result["missing"]["verifier"]["goal_pass"] is None
    assert adapter.prepared == ["pass", "fail", "unknown", "error"]
    native = json.loads(EvaluationReportAdapter.dump_json(report))
    assert len(native["cases"]) == 5
    assert all(not row["evaluator_failures"] for row in native["cases"])
    assert native["cases"][2]["labels"]["goal"]["value"] == "unknown"


@pytest.mark.asyncio
async def test_verified_business_effect_is_separate_from_execution_error(tmp_path: Path) -> None:
    adapter = SavedAdapter()
    bundle = _bundle([{"id": "pass", "answer": "correct", "execution_status": "error"}])
    graded, _ = await grade_bundle(bundle, tmp_path, adapter, RunConfig())  # type: ignore[arg-type]
    verifier = graded["runs"][0]["cases"][0]["verifier"]
    assert verifier["goal_pass"] is True
    assert verifier["checks"][-1]["id"] == "saved_execution_completed"
    assert verifier["checks"][-1]["status"] == "fail"


def test_verifier_contract_preserves_details_and_rejects_non_boolean_verdicts() -> None:
    original = {
        "status": "available",
        "goal_pass": False,
        "checks": [{"id": "answer", "status": "fail", "actual": "bad", "expected": "good"}],
    }
    validated = Verification.model_validate(original).model_dump(mode="json")
    assert validated["checks"][0]["actual"] == "bad"
    assert validated["checks"][0]["expected"] == "good"
    with pytest.raises(ValueError):
        Verification.model_validate({**original, "goal_pass": "true"})


@pytest.mark.asyncio
async def test_mismatched_input_and_unassigned_rows_cannot_claim_a_goal(tmp_path: Path) -> None:
    adapter = SavedAdapter()
    capture = _bundle(
        [
            {
                "id": "pass",
                "answer": "correct",
                "execution_status": "completed",
                "input": {"task": "a different question"},
            }
        ]
    )
    graded, _ = await grade_bundle(capture, tmp_path, adapter, RunConfig())  # type: ignore[arg-type]
    assert graded["runs"][0]["cases"][0]["verifier"]["goal_pass"] is None
    assert not adapter.prepared
    with pytest.raises(ValueError, match="unassigned"):
        await grade_bundle(_bundle([{"id": "fail"}], ["pass"]), tmp_path, adapter, RunConfig())  # type: ignore[arg-type]


async def test_custom_verifier_flags_and_metrics_survive_shared_grading(tmp_path: Path) -> None:
    class CustomAdapter(SavedAdapter):
        def grade_saved(
            self, case: AgentCase, root: Path, config: RunConfig, execution: dict[str, Any]
        ) -> dict[str, Any]:
            return {
                "status": "available",
                "goal_pass": None,
                "metrics": {"novel": 0},
                "red_flags": [{"id": "domain_flag"}],
            }

    graded, _ = await grade_bundle(
        _bundle([{"id": "pass", "execution_status": "error"}]),
        tmp_path,
        CustomAdapter(),  # type: ignore[arg-type]
        RunConfig(),
    )
    verifier = graded["runs"][0]["cases"][0]["verifier"]
    assert verifier["metrics"] == {"novel": 0}
    assert {flag["id"] for flag in verifier["red_flags"]} == {"domain_flag", "execution_incomplete"}
