"""Text-in decision service shared by product transports; uses the existing case Planner."""

from pathlib import Path

from dwelly_bot.budget import BudgetLedger
from dwelly_bot.channels.intake import Inbound
from dwelly_bot.contracts import PlannerConfig, RunConfig
from dwelly_bot.experiments.journal import Journal
from dwelly_bot.harness.runtime import CaseRuntime
from dwelly_bot.models import BudgetedModel
from dwelly_bot.planner.cli import transport
from dwelly_bot.planner.contracts import Plan, PlanDocument, PlanInput
from dwelly_bot.planner.planner import make_plan
from dwelly_bot.providers import ledger_path, profile_for


class DecisionPlanner:
    """Preserve the canonical plan instead of translating decisions into a lossy action set."""

    def __init__(self, event: Inbound, config: RunConfig, journal_path: Path) -> None:
        self.event = event
        self.config = config
        self.journal_path = journal_path
        if config.planner and config.planner.mode == "off":
            raise ValueError("A model-backed product run requires an enabled Planner")

    async def plan(self, context: str) -> Plan:
        config = self.config
        planner = config.planner or PlannerConfig()
        manager, profile = transport(planner.model or profile_for(config))
        source = PlanInput(
            case_id=self.event.scope_id,
            decision_time=self.event.received_at.isoformat(),
            request=self.event.text,
            task="Decide concrete next actions from the supplied context. Execution is simulated; no bank operation has occurred.",
            documents=[PlanDocument(name="context.md", text=context)],
            datapoints={"execution": "mock", "channel": self.event.channel},
        )
        journal = Journal(self.journal_path)
        try:
            async with manager as pool:
                model = BudgetedModel(
                    pool,
                    BudgetLedger(ledger_path(config), config.total_budget_usd),
                    f"product/{self.event.event_id}/planner",
                    config.request_timeout_seconds,
                    profile=profile,
                )
                runtime = CaseRuntime(model, config, journal)
                try:
                    return await make_plan(runtime, source, planner)
                finally:
                    journal.append(
                        {
                            "kind": "model_trace",
                            "config": config.model_dump(mode="json"),
                            "roles": runtime.role_records,
                            "costs": model.calls,
                        }
                    )
        finally:
            journal.close()
