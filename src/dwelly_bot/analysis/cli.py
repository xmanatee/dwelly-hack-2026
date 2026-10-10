"""Execute a trusted Python recipe or re-render saved analysis without recomputing it."""

from __future__ import annotations

import argparse
import asyncio
import inspect
import runpy
import uuid
from collections.abc import Sequence
from contextlib import nullcontext
from datetime import UTC, datetime
from importlib import import_module
from importlib.metadata import version
from pathlib import Path
from typing import Any

from dwelly_bot.analysis.claude_code import PREFIX as CLAUDE_CODE
from dwelly_bot.analysis.claude_code import claude_code_model, claude_code_profile
from dwelly_bot.analysis.session import AnalysisContext, validate_analysis
from dwelly_bot.budget import BudgetLedger
from dwelly_bot.configuration import read_config
from dwelly_bot.contracts import RunConfig
from dwelly_bot.models import BudgetedModel
from dwelly_bot.paths import ROOT
from dwelly_bot.providers import ledger_path as configured_ledger
from dwelly_bot.providers import model_context, profile_for
from dwelly_bot.reporting.models import Report
from dwelly_bot.storage import file_hash, fingerprint, load_json, save_json


async def execute(args: argparse.Namespace) -> Path:
    if args.recipe.endswith(".py"):
        recipe = Path(args.recipe).resolve()
        builder = runpy.run_path(str(recipe))["build"]
    else:
        builder = import_module(args.recipe).build
        recipe = Path(inspect.getfile(builder))
    settings = read_config(args.model_config) if args.model_config else RunConfig()
    if not args.data.is_dir():
        raise ValueError("The supplied data directory does not exist")
    core = Path(__file__).parent
    files = [recipe, *core.parent.rglob("*.py")]
    code = fingerprint(
        {
            "sources": {str(p): file_hash(p) for p in files},
            "dependencies": {
                name: version(name)
                for name in ["dwelly-bot", "plotly", "scikit-learn", "pydantic-ai-slim"]
            },
        }
    )
    parameters = {
        "seed": args.seed,
        "sample": args.sample,
        "text_groups": args.text_groups,
        "llm_sample": args.llm_sample,
        "deep_analysis": args.deep_analysis,
        "semantic_map": args.semantic_map,
        "screen_batch": args.screen_batch,
        "deep_sample": args.deep_sample,
        "audit_sample": args.audit_sample,
        "embedding_model": args.embedding_model,
        "embedding_provider": args.embedding_provider,
        "embedding_key_env": args.embedding_key_env,
    }
    if args.run:
        parameters["saved_run"] = str(args.run.resolve())
    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    output = (
        args.output or ROOT / "analysis/artifacts" / f"{recipe.stem}-{stamp}-{uuid.uuid4().hex[:6]}"
    )
    ctx = AnalysisContext(
        args.data,
        output,
        args.cache or ROOT / ".cache" / "analysis",
        parameters=parameters,
        code_hash=code,
        model_settings={
            "max_tokens": settings.max_tokens,
            "timeout": settings.request_timeout_seconds,
        },
    )
    try:
        if args.run:
            ctx.saved_run()
        subscription = settings.model.startswith(CLAUDE_CODE)
        transport: Any = (
            nullcontext(claude_code_model(settings.model))
            if subscription
            else model_context(profile_for(settings))
            if args.model_config
            else nullcontext(None)
        )
        async with transport as client:
            if client is not None:
                ledger_path = args.ledger
                if ledger_path is None:
                    ledger_path = configured_ledger(settings)
                elif not ledger_path.is_file():
                    raise ValueError(
                        "A custom --ledger must point to an existing shared budget file"
                    )
                ctx.model = BudgetedModel(
                    client,
                    BudgetLedger(ledger_path, settings.total_budget_usd),
                    "analysis/" + recipe.parent.name,
                    request_timeout=settings.request_timeout_seconds,
                    profile=claude_code_profile(settings)
                    if subscription
                    else client.connection_profile,
                )
            report = builder(ctx)
            if inspect.isawaitable(report):
                report = await report
            if not isinstance(report, Report):
                raise TypeError("A recipe must return Report")
            return ctx.save(report)
    except BaseException as error:
        ctx.event({"status": "error", "error": f"{type(error).__name__}: {error}"})
        save_json(ctx.output / "failed.json", {"error": str(error), "receipt": ctx.receipt()})
        raise


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="dwelly-bot analyze", description=__doc__)
    commands = parser.add_subparsers(dest="action", required=True)
    run = commands.add_parser("run", help="Execute a trusted local Python recipe")
    run.add_argument("recipe", help="Trusted importable module or Python file with build(ctx)")
    run.add_argument("--data", type=Path, required=True)
    run.add_argument(
        "--output", type=Path, help="New artifact directory; existing directories are refused"
    )
    run.add_argument("--cache", type=Path)
    run.add_argument("--sample", type=int, default=200, help="Maximum text rows for exploration")
    run.add_argument("--seed", type=int, default=0)
    run.add_argument("--text-groups", action="store_true", help="Exploratory TF-IDF groups")
    run.add_argument(
        "--model-config",
        type=Path,
        help="Opt in to paid extraction using a model/limits TOML or JSON config",
    )
    run.add_argument(
        "--ledger",
        type=Path,
        help="Override the project's shared account ledger with an existing ledger",
    )
    run.add_argument("--llm-sample", type=int, default=3)
    run.add_argument(
        "--semantic-map",
        action="store_true",
        help="Topic map without LLM screening; recipe selects the source units",
    )
    run.add_argument(
        "--deep-analysis",
        action="store_true",
        help="Full cited screening, taxonomy, semantic groups, edge cases and review",
    )
    run.add_argument("--screen-batch", type=int, default=12)
    run.add_argument("--deep-sample", type=int, default=12)
    run.add_argument("--audit-sample", type=int, default=5)
    run.add_argument(
        "--embedding-model",
        default="openai/text-embedding-3-small",
        help="Remote embedding model, or lexical for the offline TF-IDF/SVD baseline",
    )
    run.add_argument("--embedding-provider", choices=["openrouter", "openai"], default="openrouter")
    run.add_argument("--embedding-key-env", default="OPENROUTER_API_KEY")
    run.add_argument(
        "--run", type=Path, help="Read a saved benchmark bundle; never executes that benchmark"
    )
    render_parser = commands.add_parser(
        "report", help="Render saved analysis; no loaders or model calls"
    )
    render_parser.add_argument("--input", type=Path, required=True)
    render_parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    if args.action == "report":
        from dwelly_bot.reporting import render

        render(validate_analysis(Report.model_validate(load_json(args.input))), args.output)
        print(args.output.resolve())
    else:
        if args.sample < 1 or not 0 <= args.llm_sample <= 30:
            parser.error("--sample must be positive; --llm-sample must be between 0 and 30")
        if args.deep_analysis and not args.model_config:
            parser.error(
                "--deep-analysis requires --model-config; credentials are read from its configured environment variables"
            )
        if args.semantic_map and args.deep_analysis:
            parser.error("Choose --semantic-map or --deep-analysis")
        if args.semantic_map and args.embedding_model != "lexical" and not args.model_config:
            parser.error(
                "Remote embeddings require --model-config; use --embedding-model lexical for offline mapping"
            )
        if (
            not 1 <= args.screen_batch <= 30
            or not 0 <= args.deep_sample <= 100
            or not 0 <= args.audit_sample <= 30
        ):
            parser.error("Invalid screening/deep/audit batch limits")
        print(asyncio.run(execute(args)))
    return 0
