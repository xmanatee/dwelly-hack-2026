"""Regrade captured artifacts independently, without invoking a subject or model."""

from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any

from pydantic_evals import Case, Dataset
from pydantic_evals.reporting import EvaluationReport

from dwelly_bot.contracts import DatasetAdapter, RunConfig, Verification
from dwelly_bot.evaluation.checks import inspection_flags
from dwelly_bot.evaluation.runner import SavedChecks
from dwelly_bot.experiments.bundle import validate
from dwelly_bot.experiments.provenance import dataset_hash
from dwelly_bot.storage import fingerprint

_SAVED_GRADE_FIELDS = {
    "id",
    "answer",
    "public_rationale",
    "agent_disposition",
    "execution_status",
    "state_snapshots",
    "tool_events",
    "error",
}


def _unknown(reason: str, *, status: str = "unavailable") -> dict[str, Any]:
    return {"status": status, "goal_pass": None, "reason": reason, "checks": []}


def verify_bundle(
    bundle: dict[str, Any],
    dataset: Path,
    adapter: DatasetAdapter,
    config: RunConfig,
) -> dict[str, Any]:
    """Reconstruct evaluator state without subject actions or model requests.

    A verified saved state may satisfy a goal despite a separately recorded execution error.
    """
    graded = validate(copy.deepcopy(bundle))
    public_cases = {case.id: case for case in adapter.load_cases(dataset)}
    current_dataset_hash = None
    for run in graded["runs"]:
        declared_dataset_hash = run.get("manifest", {}).get("dataset_hash")
        if declared_dataset_hash is not None:
            if current_dataset_hash is None:
                current_dataset_hash = dataset_hash(dataset)
            if declared_dataset_hash != current_dataset_hash:
                raise ValueError("Saved run dataset fingerprint differs from the evaluation corpus")
            run["manifest"]["verified_dataset_hash"] = current_dataset_hash
        for execution in run["cases"]:
            case_id = execution["id"]
            missing = execution.get("execution_status") == "missing_result"
            case = public_cases.get(case_id)
            if missing:
                raw_verifier = _unknown("Assigned case has no saved execution artifact")
            elif case is None:
                raw_verifier = _unknown("Case ID is absent from the supplied evaluation dataset")
            elif declared_dataset_hash is not None and "input" not in execution:
                raw_verifier = _unknown("Saved production result has no captured case input")
            elif "input" in execution and execution["input"] != case.input:
                raw_verifier = _unknown(
                    "Saved case input differs from the supplied evaluation case"
                )
            elif "input_hash" in execution and execution["input_hash"] != fingerprint(case.input):
                raw_verifier = _unknown("Saved case input fingerprint does not match its input")
            else:
                # Captured/model-produced grades, metadata and scores have no evaluator authority.
                saved = {
                    key: copy.deepcopy(value)
                    for key, value in execution.items()
                    if key in _SAVED_GRADE_FIELDS
                }
                try:
                    raw_verifier = adapter.grade_saved(case, dataset, config, saved)
                except Exception as error:
                    raw_verifier = _unknown(
                        f"{type(error).__name__}: {error}",
                        status="error",
                    )
            try:
                verifier = Verification.model_validate(raw_verifier).model_dump(mode="json")
                if any(check["id"] == "saved_execution_completed" for check in verifier["checks"]):
                    raise ValueError("Saved execution check ID is reserved")
                json.dumps(verifier, allow_nan=False)
            except (ValueError, TypeError, KeyError) as error:
                verifier = _unknown(f"Invalid verifier contract: {error}", status="error")
            verifier["checks"].append(
                {
                    "id": "saved_execution_completed",
                    "label": "Saved execution completed",
                    "status": "unknown"
                    if missing
                    else ("pass" if execution.get("execution_status") == "completed" else "fail"),
                    "reason": "No saved result"
                    if missing
                    else str(execution.get("execution_status", "Not recorded")),
                    "dimension": "execution",
                }
            )
            execution["verifier"] = verifier
            flags = verifier.setdefault("red_flags", [])
            known = {flag["id"] for flag in flags}
            flags.extend(flag for flag in inspection_flags(execution) if flag["id"] not in known)
        run["manifest"]["evaluator_version"] = "saved-dataset-verifiers-v1"
    return graded


async def grade_bundle(
    bundle: dict[str, Any],
    dataset: Path,
    adapter: DatasetAdapter,
    config: RunConfig,
) -> tuple[dict[str, Any], EvaluationReport[Any, Any, Any]]:
    graded = verify_bundle(bundle, dataset, adapter, config)
    evaluation = Dataset(
        name=f"{adapter.name}-saved-verification",
        cases=[
            Case(name=f"{run['id']}/{case['id']}", inputs=case)
            for run in graded["runs"]
            for case in run["cases"]
        ],
        evaluators=[SavedChecks()],
    )

    report = await evaluation.evaluate(
        lambda row: row, max_concurrency=config.case_concurrency, progress=False
    )
    if report.failures or any(case.evaluator_failures for case in report.cases):
        raise RuntimeError("Pydantic Evals failed to publish saved verification results")
    return graded, report
