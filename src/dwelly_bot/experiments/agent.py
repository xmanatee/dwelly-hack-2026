"""Bounded concurrent capture with immutable observations and safe restart handling."""

from __future__ import annotations

import asyncio
import hashlib
import json
import re
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from dwelly_bot.adapters.registry import adapter_for
from dwelly_bot.budget import BudgetLedger
from dwelly_bot.contracts import AgentCase, DatasetAdapter, RunConfig
from dwelly_bot.evaluation.saved import grade_bundle
from dwelly_bot.experiments.journal import capture_case, recover_events
from dwelly_bot.experiments.provenance import (
    dataset_hash,
    execution_hash,
    git_receipt,
    grading_profile,
    source_hash,
)
from dwelly_bot.harness.runtime import CaseRuntime
from dwelly_bot.models import BudgetedModel
from dwelly_bot.paths import ROOT
from dwelly_bot.providers import ledger_path, model_context, profile_for
from dwelly_bot.reporting.html import render
from dwelly_bot.reporting.monitor import progress
from dwelly_bot.storage import json_bytes, save_json


def saved_attempt(directory: Path, case: AgentCase) -> dict[str, Any]:
    path = directory / "execution.json"
    if path.exists():
        row = json.loads(path.read_text())
        if (
            not isinstance(row, dict)
            or row.get("id") != case.id
            or row.get("input") != case.input
            or row.get("execution_status") not in {"completed", "error", "cancelled", "unconfirmed"}
        ):
            raise ValueError("Saved case identity/input/status differs from the assigned case")
        row.pop("previous_attempts", None)
        return row
    path = directory / "input.json"
    if path.exists():
        original = json.loads(path.read_text())
        if (
            not isinstance(original, dict)
            or original.get("id") != case.id
            or original.get("input") != case.input
        ):
            raise ValueError("Interrupted case input differs from the assigned case")
    return {
        "id": case.id,
        "title": case.title,
        "input": case.input,
        "execution_status": "unconfirmed",
        "stop_reason": "interrupted",
        "error": "Process stopped before a final execution record was saved",
        "tool_events": recover_events(directory / "tools.jsonl")
        if (directory / "tools.jsonl").exists()
        else [],
        "state_snapshots": {},
        "verifier": {"status": "not_run"},
    }


async def capture_cases(
    adapter: DatasetAdapter,
    dataset: Path,
    cases: list[AgentCase],
    config: RunConfig,
    model: Any,
    ledger: BudgetLedger,
    directory: Path,
    bundle: dict[str, Any],
    *,
    verbose: bool = False,
) -> dict[str, Any]:
    """Reuse completed cases; explicitly resumed static cases retain every earlier attempt."""
    if adapter.state_mode == "shared" and config.case_concurrency != 1:
        raise ValueError("Shared adapter state requires sequential case execution")
    run = bundle["runs"][0]
    ids = [case.id for case in cases]
    if not ids or len(set(ids)) != len(ids) or ids != run["manifest"]["assigned_case_ids"]:
        raise ValueError("Capture cases must match unique assigned case IDs in order")
    json.dumps([case.input for case in cases], allow_nan=False)
    rows: dict[str, dict[str, Any]] = {}
    semaphore = asyncio.Semaphore(config.case_concurrency)
    stop_reason = "interrupted"
    active: set[str] = set()

    def checkpoint() -> None:
        run["cases"] = [rows[c.id] for c in cases if c.id in rows]
        progress(directory, run, active, ledger.summary())

    async def one(index: int, case: AgentCase) -> None:
        nonlocal stop_reason
        async with semaphore:
            case_directory = directory / f"{index:04d}"
            previous: list[dict[str, Any]] = []
            if case_directory.exists():
                try:
                    attempts = [
                        case_directory,
                        *sorted((case_directory / "attempts").glob("[0-9]*")),
                    ]
                    previous = [saved_attempt(path, case) for path in attempts]
                    recovered = {**previous[-1], "previous_attempts": previous[:-1]}
                    rows[case.id] = recovered
                    if (
                        recovered["execution_status"] == "completed"
                        or adapter.state_mode != "static"
                    ):
                        if recovered["execution_status"] == "unconfirmed":
                            recovered["agent_disposition"] = "escalated"
                        checkpoint()
                        return
                    case_directory = case_directory / "attempts" / f"{len(attempts):04d}"
                except (ValueError, OSError, KeyError, TypeError) as error:
                    rows[case.id] = {
                        "id": case.id,
                        "title": case.title,
                        "input": case.input,
                        "execution_status": "unconfirmed",
                        "stop_reason": "invalid_capture",
                        "error": f"Invalid recovery artifact ({type(error).__name__}); inspect original files before retry",
                        "verifier": {"status": "not_run"},
                    }
                    checkpoint()
                    return
            if (
                stop_reason == "budget"
                or ledger.summary()["exposure_usd"] >= config.total_budget_usd - 0.05
            ):
                stop_reason = "budget"
                return
            if verbose:
                print(f"[{index}/{len(cases)}] {case.id}", flush=True)
            active.add(case.id)
            checkpoint()
            bounded_model = BudgetedModel(
                model,
                ledger,
                f"{run['id']}/{case.id}/subject",
                config.request_timeout_seconds,
                profile=profile_for(config),
            )
            session = None
            preparation_error: Exception | None = None
            try:
                session = adapter.prepare(case, dataset, config)
            except Exception as error:
                preparation_error = error
            holder: dict[str, CaseRuntime] = {}

            async def subject(inputs: dict[str, Any], journal: Any) -> dict[str, Any]:
                if session is None:
                    raise RuntimeError(
                        f"Adapter preparation failed: {type(preparation_error).__name__}: {preparation_error}"
                    ) from preparation_error
                runtime = CaseRuntime(bounded_model, config, journal)
                holder["runtime"] = runtime
                result = await session.run(runtime)
                return result.model_dump(mode="json")

            execution = None
            try:
                public_case = {
                    "id": case.id,
                    "title": case.title,
                    "input": case.input,
                    "sources": case.sources,
                }
                execution = await capture_case(
                    public_case,
                    case_directory,
                    subject,
                    session.snapshot if session else None,
                    timeout=config.case_timeout_seconds,
                )
            finally:
                if execution is None and (case_directory / "execution.json").exists():
                    execution = json.loads((case_directory / "execution.json").read_text())
                calls = bounded_model.calls
                known = sum(c["cost_usd"] for c in calls if c["status"] == "settled")
                uncertain = [c for c in calls if c["status"] == "uncertain"]
                if execution is not None:
                    if previous:
                        execution["previous_attempts"] = previous
                    if execution.get("stop_reason") == "budget":
                        stop_reason = "budget"
                    runtime = holder.get("runtime")
                    if runtime:
                        execution["usage"] = json.loads(json_bytes(runtime.usage))
                        execution["model_roles"] = runtime.role_records
                    execution["metrics"].update(
                        cost_usd=None if uncertain else known,
                        known_model_cost_usd=known,
                        unconfirmed_exposure_usd=sum(c["reserved_usd"] for c in uncertain),
                        cost_kind="provider_reported_or_disclosed_upper_bound",
                    )
                    execution["model_costs"] = calls
                    save_json(case_directory / "execution.json", execution, overwrite=True)
                    rows[case.id] = execution
                active.discard(case.id)
                checkpoint()
            if verbose and execution:
                print(
                    f"  {case.id}: {execution['execution_status']} · {len(calls)} requests · ${known:.4f}",
                    flush=True,
                )

    duration = config.run_timeout_seconds
    if config.deadline_utc:
        deadline = datetime.fromisoformat(config.deadline_utc.replace("Z", "+00:00"))
        duration = min(duration, (deadline - datetime.now(UTC)).total_seconds())
    try:
        if duration <= 0:
            stop_reason = "deadline"
        else:
            async with asyncio.timeout(duration), asyncio.TaskGroup() as tasks:
                for i, case in enumerate(cases, 1):
                    tasks.create_task(one(i, case))
    except TimeoutError:
        stop_reason = "deadline"
    except asyncio.CancelledError:
        stop_reason = "cancelled"
        raise
    finally:
        for row in rows.values():
            if row.get("execution_status") == "cancelled":
                row["stop_reason"] = stop_reason
        for case in cases:
            rows.setdefault(
                case.id,
                {
                    "id": case.id,
                    "title": case.title,
                    "input": case.input,
                    "execution_status": "not_started",
                    "stop_reason": stop_reason,
                    "error": f"Run stopped: {stop_reason}",
                    "verifier": {"status": "not_run"},
                },
            )
        unfinished = [row for row in rows.values() if row["execution_status"] != "completed"]
        run["manifest"]["incomplete_cases"] = len(unfinished)
        if unfinished:
            print(
                f"Run incomplete: {len(unfinished)} cases; stop reasons: {', '.join(sorted({row.get('stop_reason', 'execution_error') for row in unfinished}))}. Saved run: {directory}",
                flush=True,
            )
        checkpoint()
        run["manifest"]["source_changed_during_run"] = source_hash(config.skills) != run[
            "manifest"
        ].get("code_revision")
        if run["manifest"].get("execution_hash"):
            run["manifest"]["execution_changed_during_run"] = (
                execution_hash(config.skills) != run["manifest"]["execution_hash"]
            )
        run["manifest"]["budget"] = ledger.summary()
        save_json(directory / "results.json.gz", bundle, overwrite=True)
    return bundle


class RunFailure(RuntimeError):
    def __init__(self, directory: Path | None, error: Exception) -> None:
        self.directory = directory
        super().__init__(f"{type(error).__name__}: {error}")


async def execute(
    dataset_name: str,
    config: RunConfig,
    *,
    dataset_root: Path | None = None,
    ids: list[str] | None = None,
    limit: int = 0,
    experiment: str = "baseline",
    artifacts: Path | None = None,
    resume: Path | None = None,
) -> Path:
    directory = None
    try:
        if limit < 0:
            raise ValueError("Case limit must be nonnegative")
        if ids is not None and (not ids or any(not id for id in ids) or len(set(ids)) != len(ids)):
            raise ValueError("Selected case IDs must be nonempty and unique")
        if not re.fullmatch(r"[a-zA-Z0-9_-]+", experiment):
            raise ValueError("Use a plain experiment name")
        adapter = adapter_for(dataset_name)
        dataset = dataset_root or adapter.dataset_root
        input_fingerprint = dataset_hash(dataset)
        total = len(adapter.load_cases(dataset))
        selected = adapter.load_cases(dataset, ids)
        if limit:
            selected = selected[:limit]
        if not selected:
            raise ValueError("No cases selected")
        stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
        run_id = f"{stamp}-{dataset_name}-{hashlib.sha256(config.model.encode()).hexdigest()[:6]}-{uuid.uuid4().hex[:4]}"
        directory = (
            resume or (artifacts or ROOT / "experiments" / experiment / "artifacts") / run_id
        )
        captured_execution_hash = execution_hash(config.skills)
        if resume:
            manifest = json.loads((directory / "manifest.json").read_text())
            if (
                manifest["code_revision"] != source_hash(config.skills)
                or manifest["dataset_hash"] != input_fingerprint
            ):
                raise ValueError(
                    "Resume requires the same source and corpus; reconcile interrupted cases before changing either"
                )
            operational = {
                "case_concurrency",
                "run_timeout_seconds",
                "deadline_utc",
                "total_budget_usd",
                "account_budget_usd",
                "budget_file",
            }
            original = RunConfig.model_validate(manifest["resolved_config"])
            if original.model_dump(exclude=operational) != config.model_dump(
                exclude=operational
            ) or manifest["assigned_case_ids"] != [c.id for c in selected]:
                raise ValueError(
                    "Resume requires the original agent configuration and assigned cases"
                )
            run_id, captured_source_hash = manifest["id"], manifest["code_revision"]
        else:
            directory.mkdir(parents=True, exist_ok=False)
            captured_source_hash = source_hash(config.skills)
        ledger = BudgetLedger(ledger_path(config), config.total_budget_usd)
        async with model_context(profile_for(config)) as base_model:
            run: dict[str, Any] = {
                "id": run_id,
                "label": f"{dataset_name} · {config.model}",
                "cases": [],
                "manifest": {
                    "dataset": dataset_name,
                    "assigned_case_ids": [c.id for c in selected],
                    "dataset_hash": input_fingerprint,
                    "dataset_hash_algorithm": "corpus-files-v2",
                    "environment_version": "local-data:" + input_fingerprint,
                    "state_mode": adapter.state_mode,
                    "resolved_config": config.model_dump(),
                    "model": config.model,
                    "code_revision": captured_source_hash,
                    "execution_hash": captured_execution_hash,
                    **(
                        {k: manifest[k] for k in ("git_commit", "git_dirty")}
                        if resume
                        else git_receipt()
                    ),
                    "total_available_cases": total,
                    "selected_cases": len(selected),
                    "recorded_at": datetime.now(UTC).isoformat(),
                },
            }
            bundle = {
                "schema_version": 1,
                "title": "Operational agent runs",
                "runs": [run],
                "notice": "Actual model execution. Dataset labels remain evaluator-only. No independent model judge was run.",
                "attribution": "dwelly-bot code Apache 2.0; corpus provenance is retained in its source receipt.",
            }
            run["manifest"]["id"] = run_id
            if not (directory / "manifest.json").exists():
                save_json(directory / "manifest.json", run["manifest"])
            captured = await capture_cases(
                adapter,
                dataset,
                selected,
                config,
                base_model,
                ledger,
                directory,
                bundle,
                verbose=True,
            )
        # Grade persisted observations with the shared saved-artifact path.
        graded, _ = await grade_bundle(captured, dataset, adapter, config)
        grading_profile(graded, dataset, dataset_name)
        output = directory / "results.json.gz"
        save_json(output, graded, overwrite=True)
        render(graded, directory / "report.html")
        progress(directory, graded["runs"][0], set(), ledger.summary())
        rows = graded["runs"][0]["cases"]
        passed = sum(row["verifier"].get("goal_pass") is True for row in rows)
        print(
            f"Verified goals: {passed}/{len(selected)} selected cases. Report: {directory / 'report.html'}"
        )
        print(f"Shared budget: {json.dumps(ledger.summary())}")
        return output
    except Exception as error:
        raise RunFailure(directory, error) from error
