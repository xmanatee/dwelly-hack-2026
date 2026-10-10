"""Mock actions; model-driven gathering is enabled only by explicit configuration."""

import argparse
import asyncio
from collections.abc import Sequence
from pathlib import Path

from dwelly_bot.channels.intake import inbound_adapter
from dwelly_bot.context.collector import ContextCollector, ContextSource, Investigator
from dwelly_bot.context.sources import JsonSource, SQLiteSource
from dwelly_bot.execution import MockExecutor
from dwelly_bot.execution.contracts import ExecutionResult
from dwelly_bot.harness.production import ProductionPipeline
from dwelly_bot.planning import HumanReviewPlanner, Plan, Planner


class FixturePlanner:
    """Exercise an explicit saved plan without implementing Vera's planner."""

    def __init__(self, plan: Plan) -> None:
        self.value = plan

    async def plan(self, context: str) -> Plan:
        return self.value


async def run_demo(args: argparse.Namespace) -> ExecutionResult:
    event = inbound_adapter.validate_json(args.input.read_text())
    sources: list[ContextSource] = []
    if args.records:
        sources.append(JsonSource(args.records))
    if args.sqlite:
        sources.append(SQLiteSource(args.sqlite, table=args.table))
    if args.state and any(
        args.state.resolve() == p.resolve()
        for p in (args.input, args.records, args.sqlite, args.plan, args.context_config)
        if p
    ):
        raise ValueError("Receipt state must be separate from input/source files")
    if args.output.exists():
        raise FileExistsError(f"Capture directory already exists: {args.output}")
    planner: Planner = (
        FixturePlanner(Plan.model_validate_json(args.plan.read_text()))
        if args.plan
        else HumanReviewPlanner()
    )

    async def run(investigator: Investigator | None = None) -> ExecutionResult:
        return await ProductionPipeline(
            ContextCollector(tuple(sources), investigator=investigator),
            planner,
            MockExecutor(state_path=args.state),
        ).run(event, args.output)

    if not args.context_config:
        return await run()
    from dwelly_bot.budget import BudgetLedger
    from dwelly_bot.configuration import read_config
    from dwelly_bot.context.investigator import AgentInvestigator
    from dwelly_bot.models import BudgetedModel
    from dwelly_bot.providers import ledger_path, model_context, profile_for

    config = read_config(args.context_config)
    profile = profile_for(config)
    async with model_context(profile) as pool:
        model = BudgetedModel(
            pool,
            BudgetLedger(ledger_path(config), config.total_budget_usd),
            f"context/{event.event_id}",
            config.request_timeout_seconds,
            profile=profile,
        )
        return await run(AgentInvestigator(model, config))


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Mock actions; offline context unless --context-config explicitly selects a model."
    )
    parser.add_argument("--input", required=True, type=Path, help="Email, call or ticket JSON")
    parser.add_argument("--records", type=Path, help="Normalized JSON context records")
    parser.add_argument("--sqlite", type=Path, help="Read-only normalized database")
    parser.add_argument("--table", default="context_records", help="Configured SQLite table/view")
    parser.add_argument(
        "--context-config",
        type=Path,
        help="Explicit paid context-agent RunConfig; omitted means offline",
    )
    parser.add_argument(
        "--plan", type=Path, help="Saved Plan JSON; omitted means human-review stub"
    )
    parser.add_argument("--state", type=Path, help="Separate SQLite file for durable mock receipts")
    parser.add_argument("--output", required=True, type=Path, help="New capture directory")
    args = parser.parse_args(argv)
    try:
        result = asyncio.run(run_demo(args))
    except (OSError, ValueError) as exc:
        parser.exit(2, f"Demo failed: {exc}\n")
    print(f"MOCK {result.status}: {args.output / 'result.json'}")
    for receipt in result.receipts:
        print(f"  {receipt.status}: {receipt.operation} -> {receipt.target}")
    return 1 if result.status == "failed" else 0


if __name__ == "__main__":
    raise SystemExit(main())
