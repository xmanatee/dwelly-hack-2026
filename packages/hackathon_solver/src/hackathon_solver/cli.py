"""hackathon-solver generate: saved plans + visible context -> ANSWER.md / REASONING.md."""

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
from dwelly_bot.models import BudgetedModel
from dwelly_bot.planning.contracts import Plan
from dwelly_bot.providers import ledger_path, profile_for
from hackathon_solver.export import check_output, write_case
from hackathon_solver.generation import Generator, ModelGenerator, TemplateGenerator


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
    args = parser.parse_args(argv)
    return asyncio.run(generate(args))
