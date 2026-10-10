"""hackathon-solver generate: saved plans + visible context -> ANSWER.md / REASONING.md."""

from __future__ import annotations

import argparse
import asyncio
import os
from collections.abc import Sequence
from contextlib import AbstractAsyncContextManager, nullcontext
from pathlib import Path
from typing import Any

from pydantic import BaseModel

from dwelly_bot.budget import BudgetLedger
from dwelly_bot.configuration import read_config
from dwelly_bot.models import BudgetedModel
from dwelly_bot.planning.contracts import Plan
from dwelly_bot.providers import ledger_path, profile_for
from hackathon_solver.export import check_output, write_case
from hackathon_solver.generation import Generator, ModelGenerator, TemplateGenerator


class PlannerFailure(BaseModel):
    status: str = "error"
    error: str


def cases(directory: Path) -> list[tuple[str, Plan, str]]:
    found = []
    for path in sorted(directory.glob("*.plan.json")):
        case_id = path.name.removesuffix(".plan.json")
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
    async with context as base:
        for case_id, plan, text in inputs:
            generator: Generator
            if base is None:
                generator, details = TemplateGenerator(), {"kind": "template"}
            else:
                assert ledger is not None
                model = BudgetedModel(
                    base,
                    ledger,
                    f"generation/{case_id}",
                    config.request_timeout_seconds,
                    profile=profile,
                )
                generator, details = ModelGenerator(model), {"kind": "model", "model": config.model}
            generated = await generator.generate(plan, text)
            write_case(args.output, case_id, generated, plan=plan, context=text, generator=details)
            print(f"  {case_id}: written", flush=True)
    print(f"{len(inputs)} cases. Output: {args.output}")
    return 0


async def predict(args: argparse.Namespace) -> int:
    """Case evidence -> case planner -> generator -> two files, for every selected case."""
    from datetime import UTC, datetime

    from dwelly_bot.adapters.registry import adapter_for
    from dwelly_bot.contracts import PlannerConfig
    from dwelly_bot.experiments.journal import Journal
    from dwelly_bot.harness.runtime import CaseRuntime
    from dwelly_bot.planner.cli import transport
    from dwelly_bot.planner.contracts import Plan as CasePlan
    from dwelly_bot.planner.planner import plan_case
    from dwelly_bot.storage import save_json
    from hackathon_solver.generation import Generated

    config = read_config(args.config)
    adapter = adapter_for(args.dataset)
    root = args.dataset_root or adapter.dataset_root
    selected = adapter.load_cases(root, args.ids.split(",") if args.ids else None)
    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    output = args.output or Path("experiments/banking-predictions/artifacts") / stamp
    development = args.dataset == "dwelly-banking"
    check_output(output, development=development)
    output.mkdir(parents=True, exist_ok=True)
    context, profile = transport(profile_for(config))
    ledger = BudgetLedger(ledger_path(config), config.total_budget_usd)
    semaphore = asyncio.Semaphore(config.case_concurrency)
    rows: list[dict[str, Any]] = []
    async with context as base:

        def bounded(name: str) -> BudgetedModel:
            return BudgetedModel(
                base, ledger, name, config.request_timeout_seconds, profile=profile
            )

        async def one(case: Any) -> None:
            async with semaphore:
                session = adapter.prepare(case, root, config)
                source = session.plan_input(config)  # type: ignore[attr-defined]
                text = "\n\n".join(
                    f"## {name}\n\n{path.read_text()}"
                    for name, path in session.documents.files.items()  # type: ignore[attr-defined]
                )
                journal = Journal(output / "journals" / f"{case.id}.jsonl")
                planner_model, generator_model = bounded(f"predict/{case.id}/planner"), None
                try:
                    planned = await plan_case(
                        CaseRuntime(planner_model, config, journal),
                        source,
                        config.planner or PlannerConfig(),
                    )
                finally:
                    journal.file.close()
                details: dict[str, Any] = {"planner": planned.get("error") or "available"}
                if planned["status"] == "available":
                    plan: Any = CasePlan.model_validate(planned["plan"])
                    if args.template:
                        generated = await TemplateGenerator().generate(plan, text)
                        details["kind"] = "template"
                    else:
                        generator_model = bounded(f"predict/{case.id}/generator")
                        generated = await ModelGenerator(generator_model).generate(plan, text)
                        details.update(kind="model", model=config.model)
                else:
                    plan = PlannerFailure(error=str(planned.get("error")))
                    generated = Generated(
                        answer="Processing did not produce a plan; this case requires human review.",
                        reasoning=f"Planner error: {planned.get('error')}",
                    )
                    details["kind"] = "planner_error"
                write_case(output, case.id, generated, plan=plan, context=text, generator=details)
                calls = planner_model.calls + (generator_model.calls if generator_model else [])
                rows.append(
                    {
                        "case_id": case.id,
                        "planner": planned["status"],
                        "generator": details["kind"],
                        "requests": len(calls),
                        "cost_usd": sum(c["cost_usd"] for c in calls if c["status"] == "settled"),
                    }
                )
                print(f"  {case.id}: {planned['status']} / {details['kind']}", flush=True)

        await asyncio.gather(*(one(case) for case in selected))
    order = {case.id: i for i, case in enumerate(selected)}
    rows.sort(key=lambda row: order[row["case_id"]])
    save_json(
        output / "predictions.json", {"dataset": args.dataset, "root": str(root), "cases": rows}
    )
    if development:
        (output / "README.md").write_text(
            "# Development predictions\n\nPublic practice cases, not Reality Test results. "
            "Do not submit them.\n"
        )
    failed = sum(row["planner"] != "available" for row in rows)
    print(f"{len(rows)} cases, {failed} planner errors. Output: {output}")
    return 0


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
    case = commands.add_parser("predict", help="Plan and generate answers for dataset cases")
    case.add_argument("--dataset", default="dwelly-banking")
    case.add_argument("--dataset-root", type=Path)
    case.add_argument("--ids", help="Comma-separated case IDs")
    case.add_argument("--config", type=Path, required=True, help="Planner/generator run config")
    case.add_argument("--output", type=Path, help="Empty directory; default under experiments")
    case.add_argument("--template", action="store_true", help="Deterministic generator")
    args = parser.parse_args(argv)
    return asyncio.run(predict(args) if args.command == "predict" else generate(args))
