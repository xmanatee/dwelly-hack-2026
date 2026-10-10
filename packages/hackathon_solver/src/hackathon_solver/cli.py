"""hackathon-solver generate: saved plans + visible context -> ANSWER.md / REASONING.md."""

from __future__ import annotations

import argparse
import asyncio
import os
from collections.abc import Sequence
from contextlib import AbstractAsyncContextManager, AsyncExitStack, nullcontext
from pathlib import Path
from typing import Any

from pydantic import BaseModel

from dwelly_bot.budget import BudgetLedger
from dwelly_bot.configuration import read_config
from dwelly_bot.experiments.journal import Journal
from dwelly_bot.harness.runtime import CaseRuntime
from dwelly_bot.models import BudgetedModel
from dwelly_bot.planning.contracts import Plan
from dwelly_bot.providers import ledger_path, profile_for
from dwelly_bot.storage import save_json
from hackathon_solver.export import CASE, check_output, write_case
from hackathon_solver.generation import Generated, Generator, ModelGenerator, TemplateGenerator


class PlannerFailure(BaseModel):
    status: str = "error"
    error: str


def cases(directory: Path) -> list[tuple[str, Plan, str]]:
    found = []
    for path in sorted(directory.glob("*.plan.json")):
        case_id = path.name.removesuffix(".plan.json")
        if not CASE.fullmatch(case_id):
            raise ValueError(f"Unsafe case identifier {case_id!r}")
        context = directory / f"{case_id}.context.md"
        if not context.exists():
            raise ValueError(f"{case_id}: missing {context.name}")
        found.append((case_id, Plan.model_validate_json(path.read_text()), context.read_text()))
    if not found:
        raise ValueError(f"No *.plan.json files in {directory}")
    return found


async def generate(args: argparse.Namespace) -> int:
    inputs = cases(args.input)
    check_output(args.output, development=args.development)
    context: AbstractAsyncContextManager[Any] = nullcontext(None)
    ledger = None
    if args.config:
        from dwelly_bot.planner.cli import transport

        config = read_config(args.config)
        context, profile = transport(profile_for(config))
        ledger = BudgetLedger(ledger_path(config), config.total_budget_usd)
    failed = 0
    async with context as base:
        for case_id, plan, text in inputs:
            generator: Generator
            journal = None
            runtime = None
            model = None
            details: dict[str, Any] = {"kind": "template"}
            if base is None:
                generator = TemplateGenerator()
            else:
                assert ledger is not None
                model = BudgetedModel(
                    base,
                    ledger,
                    f"generation/{case_id}",
                    config.request_timeout_seconds,
                    profile=profile,
                )
                journal = Journal(args.output / "journals" / f"{case_id}.jsonl")
                runtime = CaseRuntime(model, config, journal)
                generator = ModelGenerator(runtime)
                details = {"kind": "model", "model": config.model}
            try:
                generated = await generator.generate(plan, text)
            except Exception as exc:
                failed += 1
                details.update(kind="generator_error", error=f"{type(exc).__name__}: {exc}")
                generated = failure_notice("Generator", details["error"])
            finally:
                if journal is not None and runtime is not None and model is not None:
                    try:
                        record_trace(runtime, [model])
                    finally:
                        journal.close()
            write_case(args.output, case_id, generated, plan=plan, context=text, generator=details)
            print(f"  {case_id}: {details['kind']}", flush=True)
    print(f"{len(inputs)} cases, {failed} errors. Output: {args.output}")
    return int(failed > 0)


def failure_notice(stage: str, error: str) -> Generated:
    return Generated(
        answer="Processing could not be completed; this case requires human review.",
        reasoning=f"{stage} error: {error}",
    )


def record_trace(runtime: CaseRuntime, models: list[BudgetedModel]) -> None:
    runtime.journal.append(
        {
            "kind": "model_trace",
            "config": runtime.config.model_dump(mode="json"),
            "roles": runtime.role_records,
            "costs": [c for model in models for c in model.calls],
        }
    )


DEFAULT_CASES = Path(".cache/datasets/banking-v1/original/Banking & Financial Services")


async def predict(args: argparse.Namespace) -> int:
    """Full history.md -> case planner -> generator -> ANSWER.md and REASONING.md."""
    from datetime import UTC, datetime

    from dwelly_bot.contracts import PlannerConfig
    from dwelly_bot.planner.cli import transport
    from dwelly_bot.planner.contracts import Plan as CasePlan
    from dwelly_bot.planner.planner import plan_case
    from hackathon_solver.adapters import HistoryCase, load
    from hackathon_solver.export.html import render

    config = read_config(args.config)
    if args.submission and args.cases.resolve().is_relative_to(DEFAULT_CASES.resolve()):
        raise ValueError("The installed public practice corpus is not a submission dataset")
    selected = load(args.cases, config, ids=args.ids.split(",") if args.ids else None)
    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    output = args.output or Path("experiments/banking-predictions/artifacts") / stamp
    development = not args.submission
    planner_config = config.planner or PlannerConfig()
    if planner_config.mode == "off":
        raise ValueError("predict requires an enabled Planner")
    check_output(output, development=development)
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
                                "kind": "template" if args.template else "model",
                            }
                            generated = (
                                await TemplateGenerator().generate(plan, case.history)
                                if args.template
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
            "input": "full history.md",
            "development": development,
            "config": config.model_dump(mode="json"),
            "cases_root": str(args.cases),
            "cases": rows,
        },
    )
    if development:
        (output / "README.md").write_text(
            "# Development predictions\n\nPublic practice cases, not Reality Test results. "
            "Do not submit them.\n"
        )
    failed = sum(row["generator"].endswith("_error") for row in rows)
    print(f"{len(rows)} cases, {failed} errors. Report: {render(output)}")
    return int(failed > 0)


def main(argv: Sequence[str] | None = None) -> int:
    os.environ["LOGFIRE_SEND_TO_LOGFIRE"] = "false"
    os.environ["OTEL_SDK_DISABLED"] = "true"
    os.environ["PYDANTIC_AI_NO_BANNER"] = "1"
    parser = argparse.ArgumentParser(prog="hackathon-solver", description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    run = commands.add_parser("generate", help="Write ANSWER.md and REASONING.md per case")
    run.add_argument(
        "--input", type=Path, required=True, help="<case>.plan.json + <case>.context.md"
    )
    run.add_argument("--output", type=Path, required=True, help="Empty output directory")
    run.add_argument("--config", type=Path, help="Run config for the model generator")
    run.add_argument(
        "--development", action="store_true", help="Practice cases: refuse an ANSWERS directory"
    )
    case = commands.add_parser(
        "predict", help="Full history.md -> ANSWER.md and REASONING.md per case"
    )
    case.add_argument(
        "--cases", type=Path, default=DEFAULT_CASES, help="Track folder of NNN/history.md"
    )
    case.add_argument(
        "--submission", action="store_true", help="Real challenge cases; allows an ANSWERS output"
    )
    case.add_argument("--ids", help="Comma-separated case IDs")
    case.add_argument("--config", type=Path, required=True, help="Planner/generator run config")
    case.add_argument("--output", type=Path, help="Empty directory; default under experiments")
    case.add_argument("--template", action="store_true", help="Deterministic generator")
    page = commands.add_parser("report", help="Write report.html for a predictions directory")
    page.add_argument("--input", type=Path, required=True)
    args = parser.parse_args(argv)
    if args.command == "report":
        from hackathon_solver.export.html import render

        print(render(args.input))
        return 0
    return asyncio.run(predict(args) if args.command == "predict" else generate(args))
