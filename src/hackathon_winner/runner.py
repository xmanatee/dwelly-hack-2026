"""Folder-to-folder Planner and answer generation; all bank actions remain proposals."""

from __future__ import annotations

import asyncio
from contextlib import AsyncExitStack
from pathlib import Path
from typing import Any

from pydantic import BaseModel

from dwelly_bot.budget import BudgetLedger
from dwelly_bot.configuration import read_config
from dwelly_bot.contracts import RunConfig
from dwelly_bot.experiments.journal import Journal
from dwelly_bot.harness.runtime import CaseRuntime
from dwelly_bot.models import BudgetedModel
from dwelly_bot.paths import ROOT
from dwelly_bot.providers import ledger_path, profile_for
from dwelly_bot.storage import save_json
from hackathon_winner.export import check_output, write_case
from hackathon_winner.generation import ModelGenerator, TemplateGenerator
from hackathon_winner.tracing import PlannerFailure, failure_notice, record_trace

PACKAGE = Path(__file__).resolve().parent
DEFAULT_CASES = PACKAGE / "data/cases"
DEFAULT_CONFIG = PACKAGE / "config.json"
DEFAULT_OUTPUT = ROOT / "ANSWERS"


async def run_cases(
    cases: Path = DEFAULT_CASES,
    *,
    output: Path = DEFAULT_OUTPUT,
    config: RunConfig | None = None,
    ids: list[str] | None = None,
    template: bool = False,
) -> int:
    """Full history.md -> case planner -> generator -> ANSWER.md and REASONING.md."""
    from dwelly_bot.contracts import PlannerConfig
    from dwelly_bot.planner import Plan as CasePlan
    from dwelly_bot.planner import plan_case
    from dwelly_bot.planner.cli import transport
    from hackathon_winner.adapters import HistoryCase, load
    from hackathon_winner.export.html import render

    config = config or read_config(DEFAULT_CONFIG)
    selected = load(cases, config, ids=ids, prefix="")
    development = (
        cases.resolve().is_relative_to(DEFAULT_CASES.resolve())
        or cases.resolve()
        == (ROOT / ".cache/datasets/banking-v1/original/Banking & Financial Services").resolve()
    )
    if output.resolve() == cases.resolve() or output.resolve().is_relative_to(cases.resolve()):
        raise ValueError("Output must be outside the input cases directory")
    planner_config = config.planner or PlannerConfig()
    if planner_config.mode == "off":
        raise ValueError("predict requires an enabled Planner")
    check_output(output, development=False)
    output.mkdir(parents=True, exist_ok=True)
    context, profile = transport(profile_for(config))
    planner_context, planner_profile = transport(planner_config.model or profile_for(config))
    ledger = BudgetLedger(ledger_path(config), config.total_budget_usd)
    semaphore = asyncio.Semaphore(config.case_concurrency)
    rows: list[dict[str, Any]] = []
    async with AsyncExitStack() as stack:
        base = await stack.enter_async_context(context)
        planner_base = (
            await stack.enter_async_context(planner_context) if planner_config.model else base
        )

        async def one(case: HistoryCase) -> None:
            async with semaphore:
                journal = Journal(output / "journals" / f"{case.case_id}.jsonl")
                planner_model = BudgetedModel(
                    planner_base,
                    ledger,
                    f"predict/{case.case_id}/planner",
                    config.request_timeout_seconds,
                    profile=planner_profile,
                )
                generator_model = BudgetedModel(
                    base,
                    ledger,
                    f"predict/{case.case_id}/generator",
                    config.request_timeout_seconds,
                    profile=profile,
                )
                runtime = CaseRuntime(generator_model, config, journal, planner_model=planner_model)
                planned: dict[str, Any] = {"status": "error", "error": "Planner did not complete"}
                details: dict[str, Any] = {"kind": "planner_error"}
                plan: BaseModel = PlannerFailure(error="Planner did not complete")
                try:
                    async with asyncio.timeout(config.case_timeout_seconds):
                        planned = await plan_case(runtime, case.source, planner_config)
                        if planned["status"] == "available":
                            plan = CasePlan.model_validate(planned["plan"])
                            details = {
                                "planner": "available",
                                "kind": "template" if template else "model",
                            }
                            generated = (
                                await TemplateGenerator().generate(plan, case.history)
                                if template
                                else await ModelGenerator(runtime).generate(plan, case.history)
                            )
                        else:
                            plan = PlannerFailure(error=str(planned.get("error")))
                            details["error"] = planned.get("error")
                            generated = failure_notice("Planner", str(planned.get("error")))
                except Exception as exc:
                    stage = "generator" if planned["status"] == "available" else "planner"
                    details.update(kind=f"{stage}_error", error=f"{type(exc).__name__}: {exc}")
                    generated = failure_notice(stage.capitalize(), details["error"])
                finally:
                    try:
                        record_trace(runtime, [planner_model, generator_model])
                    finally:
                        journal.close()
                write_case(
                    output,
                    case.case_id,
                    generated,
                    plan=plan,
                    context=case.history,
                    generator=details,
                )
                calls = planner_model.calls + generator_model.calls
                rows.append(
                    {
                        "case_id": case.case_id,
                        "input_files": case.input_files,
                        "planner": planned["status"],
                        "generator": details["kind"],
                        "error": details.get("error"),
                        "requests": len(calls),
                        "cost_usd": sum(c["cost_usd"] for c in calls if c["status"] == "settled"),
                    }
                )
                print(f"  {case.case_id}: {planned['status']} / {details['kind']}", flush=True)

        await asyncio.gather(*(one(case) for case in selected))
    order = {case.case_id: i for i, case in enumerate(selected)}
    rows.sort(key=lambda row: order[row["case_id"]])
    save_json(
        output / "predictions.json",
        {
            "input": "supplied case context and attachments",
            "development": development,
            "config": config.model_dump(mode="json"),
            "cases_root": str(cases),
            "cases": rows,
        },
    )

    failed = sum(row["generator"].endswith("_error") for row in rows)
    print(f"{len(rows)} cases, {failed} errors. Report: {render(output)}")
    return int(failed > 0)
