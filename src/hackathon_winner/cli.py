"""Hackathon Winner: case folders -> Planner -> ANSWER.md / REASONING.md."""

from __future__ import annotations

import argparse
import asyncio
import os
from collections.abc import Sequence
from contextlib import AbstractAsyncContextManager, nullcontext
from pathlib import Path
from typing import Any

from dwelly_bot.budget import BudgetLedger
from dwelly_bot.configuration import read_config
from dwelly_bot.experiments.journal import Journal
from dwelly_bot.harness.runtime import CaseRuntime
from dwelly_bot.models import BudgetedModel
from dwelly_bot.planning.contracts import Plan
from dwelly_bot.providers import ledger_path, profile_for
from hackathon_winner.export import CASE, prepare_output, write_case
from hackathon_winner.generation import Generator, ModelGenerator, TemplateGenerator
from hackathon_winner.runner import DEFAULT_CASES, DEFAULT_CONFIG, DEFAULT_OUTPUT, run_cases
from hackathon_winner.tracing import failure_notice, record_trace


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
    prepare_output(args.output, development=args.development)
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


def main(argv: Sequence[str] | None = None) -> int:
    os.environ["LOGFIRE_SEND_TO_LOGFIRE"] = "false"
    os.environ["OTEL_SDK_DISABLED"] = "true"
    os.environ["PYDANTIC_AI_NO_BANNER"] = "1"
    import sys

    arguments = list(sys.argv[1:] if argv is None else argv)
    if not arguments or arguments[0] not in {"run", "predict", "generate", "report"}:
        arguments.insert(0, "run")
    parser = argparse.ArgumentParser(prog="hackathon-winner", description=__doc__)
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
        "run", aliases=["predict"], help="Case folders -> ANSWER.md and REASONING.md per case"
    )
    case.add_argument("directory", type=Path, nargs="?", help="Folder with one subfolder per case")
    case.add_argument("--cases", type=Path, help="Alias for the positional input folder")
    case.add_argument("--submission", action="store_true", help=argparse.SUPPRESS)
    case.add_argument("--ids", help="Comma-separated case IDs")
    case.add_argument(
        "--config", type=Path, default=DEFAULT_CONFIG, help="Planner/generator run config"
    )
    case.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT,
        help="Output folder; default: repository ANSWERS/",
    )
    case.add_argument("--template", action="store_true", help="Deterministic generator")
    page = commands.add_parser("report", help="Write report.html for a predictions directory")
    page.add_argument("--input", type=Path, required=True)
    args = parser.parse_args(arguments)
    if args.command == "report":
        from hackathon_winner.export.html import render

        print(render(args.input))
        return 0
    try:
        if args.command == "generate":
            return asyncio.run(generate(args))
        if args.directory and args.cases:
            parser.error("Use a positional folder or --cases, not both")
        return asyncio.run(
            run_cases(
                args.directory or args.cases or DEFAULT_CASES,
                output=args.output,
                config=read_config(args.config),
                ids=[item.strip() for item in args.ids.split(",") if item.strip()]
                if args.ids
                else None,
                template=args.template,
            )
        )
    except (OSError, ValueError) as exc:
        parser.exit(2, f"Hackathon Winner: {exc}\n")
