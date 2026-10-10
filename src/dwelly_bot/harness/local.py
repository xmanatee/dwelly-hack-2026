"""Shared local composition for demo fixtures and synthetic data; effects stay mock."""

from pathlib import Path
from typing import Any

from dwelly_bot.channels.intake import Inbound
from dwelly_bot.context.collector import ContextCollector, ContextSource, Investigator
from dwelly_bot.execution import MockExecutor
from dwelly_bot.execution.contracts import ExecutionResult
from dwelly_bot.harness.production import ProductionPipeline
from dwelly_bot.planning import Planner


async def run_local_pipeline(
    event: Inbound,
    sources: tuple[ContextSource, ...],
    planner: Planner,
    output: Path,
    *,
    state: Path | None = None,
    context_config: Path | None = None,
    planner_config: Path | None = None,
    dataset: dict[str, Any] | None = None,
) -> ExecutionResult:
    if output.exists():
        raise FileExistsError(f"Capture directory already exists: {output}")
    if state is not None and state.resolve().is_relative_to(output.resolve()):
        raise ValueError("Receipt state must be outside the capture directory")

    async def run(investigator: Investigator | None = None) -> ExecutionResult:
        if planner_config is not None:
            import asyncio

            from dwelly_bot.configuration import read_config
            from dwelly_bot.execution.decision import DecisionExecutor
            from dwelly_bot.planner.service import DecisionPlanner

            config = read_config(planner_config)
            async with asyncio.timeout(config.case_timeout_seconds):
                return await ProductionPipeline(
                    ContextCollector(sources, investigator=investigator),
                    DecisionPlanner(event, config, output / "planner.jsonl"),
                    DecisionExecutor(state),
                ).run(event, output, dataset=dataset)
        return await ProductionPipeline(
            ContextCollector(sources, investigator=investigator),
            planner,
            MockExecutor(state_path=state),
        ).run(event, output, dataset=dataset)

    if context_config is None:
        return await run()
    from dwelly_bot.budget import BudgetLedger
    from dwelly_bot.configuration import read_config
    from dwelly_bot.context.investigator import AgentInvestigator
    from dwelly_bot.models import BudgetedModel
    from dwelly_bot.providers import ledger_path, model_context, profile_for

    config = read_config(context_config)
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
