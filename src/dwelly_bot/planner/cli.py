"""Run the planner alone: JSON inputs or dataset cases in, checked plans out; no solver runs."""

from __future__ import annotations

import argparse
import asyncio
from collections.abc import Sequence
from contextlib import AbstractAsyncContextManager, nullcontext
from pathlib import Path
from typing import Any

from dwelly_bot.adapters.registry import adapter_for
from dwelly_bot.budget import BudgetLedger
from dwelly_bot.configuration import read_config
from dwelly_bot.contracts import ModelProfile, PlannerConfig, RunConfig
from dwelly_bot.experiments.journal import Journal
from dwelly_bot.harness.runtime import CaseRuntime
from dwelly_bot.models import BudgetedModel
from dwelly_bot.planner.contracts import PlanInput
from dwelly_bot.planner.planner import plan_case
from dwelly_bot.providers import ledger_path, model_context, profile_for
from dwelly_bot.storage import save_json


def dataset_inputs(
    name: str, root: Path | None, ids: list[str] | None, config: RunConfig
) -> list[PlanInput]:
    adapter = adapter_for(name)
    root = root or adapter.dataset_root
    inputs = []
    for case in adapter.load_cases(root, ids):
        session = adapter.prepare(case, root, config)
        builder = getattr(session, "plan_input", None)
        if builder is None:
            raise ValueError(f"The {name} adapter does not build planner input")
        inputs.append(builder(config))
    return inputs


def transport(profile: ModelProfile) -> tuple[AbstractAsyncContextManager[Any], ModelProfile]:
    """Provider pool, or the local Claude Code CLI for claude-code/<alias> models."""
    from dwelly_bot.analysis.claude_code import PREFIX, claude_code_model

    if profile.model.startswith(PREFIX):
        billing = ModelProfile(
            model=profile.model,
            provider="anthropic",
            input_price_per_million=profile.input_price_per_million or 3,
            output_price_per_million=profile.output_price_per_million or 15,
            max_tokens=profile.max_tokens,
        )
        return nullcontext(claude_code_model(profile.model)), billing
    return model_context(profile), profile


async def run(
    inputs: list[PlanInput], config: RunConfig, output: Path, *, call: bool
) -> list[dict[str, Any]]:
    planner = config.planner or PlannerConfig()
    output.mkdir(parents=True, exist_ok=False)
    for source in inputs:
        save_json(output / f"{source.case_id}.input.json", source.model_dump(mode="json"))
    if not call:
        return [{"case_id": s.case_id, "status": "not_run"} for s in inputs]
    context, profile = transport(planner.model or profile_for(config))
    ledger = BudgetLedger(ledger_path(config), config.total_budget_usd)
    semaphore = asyncio.Semaphore(config.case_concurrency)
    rows: list[dict[str, Any]] = []
    async with context as base:

        async def one(source: PlanInput) -> None:
            async with semaphore:
                model = BudgetedModel(
                    base,
                    ledger,
                    f"planner/{source.case_id}",
                    config.request_timeout_seconds,
                    profile=profile,
                )
                journal = Journal(output / "journals" / f"{source.case_id}.jsonl")
                try:
                    result = await plan_case(CaseRuntime(model, config, journal), source, planner)
                finally:
                    journal.file.close()
                save_json(output / f"{source.case_id}.plan.json", result)
                plan = result.get("plan") or {}
                rows.append(
                    {
                        "case_id": source.case_id,
                        "status": result["status"],
                        "error": result.get("error"),
                        "intent": plan.get("intent"),
                        "safety_flags": plan.get("safety_flags", []),
                        "steps": [s["action"] for s in plan.get("steps", [])],
                        "expected_disposition": plan.get("expected_disposition"),
                        "requests": len(model.calls),
                        "cost_usd": sum(
                            c["cost_usd"] for c in model.calls if c["status"] == "settled"
                        ),
                    }
                )
                print(f"  {source.case_id}: {result['status']}", flush=True)

        await asyncio.gather(*(one(source) for source in inputs))
    order = {s.case_id: i for i, s in enumerate(inputs)}
    return sorted(rows, key=lambda row: order[row["case_id"]])


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="dwelly-bot plan", description=__doc__)
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--input", type=Path, nargs="+", help="PlanInput JSON files")
    source.add_argument("--dataset", help="Registered dataset adapter, e.g. dwelly-banking")
    parser.add_argument("--dataset-root", type=Path)
    parser.add_argument("--ids", help="Comma-separated case IDs")
    parser.add_argument("--config", type=Path, required=True, help="Run config; uses `planner`")
    parser.add_argument("--output", type=Path, required=True, help="New output directory")
    parser.add_argument(
        "--inputs-only", action="store_true", help="Write planner inputs without model calls"
    )
    args = parser.parse_args(argv)
    config = read_config(args.config)
    inputs = (
        [PlanInput.model_validate_json(path.read_text()) for path in args.input]
        if args.input
        else dataset_inputs(
            args.dataset, args.dataset_root, args.ids.split(",") if args.ids else None, config
        )
    )
    rows = asyncio.run(run(inputs, config, args.output, call=not args.inputs_only))
    save_json(args.output / "plans.json", rows)
    failed = sum(row["status"] == "error" for row in rows)
    print(f"{len(rows)} cases, {failed} planner errors. Output: {args.output}")
    return 0
