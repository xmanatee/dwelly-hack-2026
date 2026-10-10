"""Execute operational cases and inspect dataset, provider and configured budget readiness."""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from collections.abc import Sequence
from pathlib import Path
from typing import Any
from urllib.request import Request, urlopen

from dwelly_bot.adapters.registry import ADAPTERS, adapter_for
from dwelly_bot.budget import BudgetLedger
from dwelly_bot.configuration import read_config, read_settings
from dwelly_bot.contracts import ModelProfile, Modules, RunConfig
from dwelly_bot.evaluation.runner import evaluation_failed
from dwelly_bot.experiments.agent import execute
from dwelly_bot.paths import ROOT
from dwelly_bot.providers import credentials, ledger_path
from dwelly_bot.storage import load_json


def key_status() -> dict[str, Any]:
    key = next(iter(credentials(ModelProfile()).values()))
    request = Request(
        "https://openrouter.ai/api/v1/key", headers={"Authorization": f"Bearer {key}"}
    )
    with urlopen(request, timeout=15) as response:
        data = json.load(response)["data"]
    # Key labels and authentication headers never enter artifacts.
    return {k: data.get(k) for k in ["limit", "limit_remaining", "usage", "is_free_tier"]}


def resolved_config(args: argparse.Namespace) -> RunConfig:
    settings = read_settings(args.config) if args.config else {}
    if args.prompt:
        settings["instructions"] = args.prompt.read_text()
    settings.update(
        {
            name: value
            for name, value in vars(args).items()
            if name in RunConfig.model_fields and value is not None
        }
    )
    settings["modules"] = {
        **settings.get("modules", {}),
        **dict.fromkeys(args.disable_module, False),
    }
    return RunConfig.model_validate(settings)


def main(argv: Sequence[str] | None = None) -> int:
    arguments = list(sys.argv[1:] if argv is None else argv)
    parser = argparse.ArgumentParser(prog="dwelly-bot agent", description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    run = commands.add_parser("run")
    run.add_argument("dataset", choices=list(ADAPTERS))
    run.add_argument("--ids", help="Comma-separated source case IDs")
    run.add_argument("--limit", type=int, default=0)
    run.add_argument("--config", type=Path, default=ROOT / "experiments/baseline/config.json")
    run.add_argument("--model")
    run.add_argument("--provider", choices=["openrouter", "openai", "anthropic"])
    run.add_argument(
        "--effort",
        dest="reasoning_effort",
        choices=["none", "minimal", "low", "medium", "high", "xhigh", "max"],
    )
    run.add_argument("--skills", nargs="+")
    run.add_argument("--skill-mode", choices=["preload", "on_demand"])
    run.add_argument(
        "--disable-domain-skill", dest="domain_skill_enabled", action="store_false", default=None
    )
    run.add_argument("--disable-tool", dest="disabled_tools", action="append")
    run.add_argument("--concurrency", dest="case_concurrency", type=int)
    run.add_argument("--run-timeout", dest="run_timeout_seconds", type=float)
    run.add_argument("--deadline", dest="deadline_utc", help="ISO timestamp with explicit timezone")
    run.add_argument("--budget-file", help="Explicit separate ledger, required above $15")
    run.add_argument("--artifacts", type=Path, help="Parent directory for new immutable runs")
    run.add_argument("--resume", type=Path)
    run.add_argument("--dataset-root", type=Path)
    run.add_argument("--experiment", default="baseline")
    run.add_argument(
        "--answers", type=Path, help="Export this run's ANSWERS into an empty directory"
    )
    run.add_argument(
        "--prompt",
        type=Path,
        help="Trusted variant instructions appended to the common/domain prompt",
    )
    run.add_argument(
        "--disable-module", action="append", default=[], choices=list(Modules.model_fields)
    )
    run.add_argument("--max-tokens", type=int)
    run.add_argument("--max-requests", type=int)
    run.add_argument("--timeout", dest="case_timeout_seconds", type=float)
    run.add_argument("--budget", dest="total_budget_usd", type=float)
    run.add_argument("--max-tool-calls", type=int)
    run.add_argument("--request-timeout", dest="request_timeout_seconds", type=float)
    budget = commands.add_parser("budget", help="Inspect the ledger selected by a run config")
    budget.add_argument("--config", type=Path, default=ROOT / "experiments/baseline/config.json")
    doctor = commands.add_parser("doctor")
    doctor.add_argument(
        "--provider", action="store_true", help="Read key allowance without model requests"
    )
    args = parser.parse_args(arguments)
    if args.command == "run":
        from dwelly_bot.reporting.submission import check_destination, export

        if args.answers:
            check_destination(args.answers, dataset=args.dataset)
        output = asyncio.run(
            execute(
                args.dataset,
                resolved_config(args),
                dataset_root=args.dataset_root,
                ids=args.ids.split(",") if args.ids is not None else None,
                limit=args.limit,
                experiment=args.experiment,
                artifacts=args.artifacts,
                resume=args.resume,
            )
        )
        saved = load_json(output)
        if args.answers:
            export(saved, args.answers)
            print(f"Submission answers: {args.answers}")
        return int(
            any(
                c["execution_status"] != "completed" or evaluation_failed(c)
                for r in saved["runs"]
                for c in r["cases"]
            )
        )
    elif args.command == "budget":
        config = read_config(args.config)
        print(
            json.dumps(
                BudgetLedger(ledger_path(config), config.total_budget_usd).summary(), indent=2
            )
        )
    else:
        for name in ADAPTERS:
            adapter = adapter_for(name)
            folder = adapter.dataset_root
            if not (folder / "source.json").is_file():
                print(name, "dataset not installed")
                continue
            print(name, len(adapter.load_cases(folder)), "cases")
        if args.provider:
            print(json.dumps(key_status(), indent=2))

    return 0
