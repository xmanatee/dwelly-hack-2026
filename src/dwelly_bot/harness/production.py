"""One orchestration path for all channels, with replaceable context/planner/executor."""

from collections.abc import Callable
from pathlib import Path
from typing import Any, Protocol

from pydantic import BaseModel

from dwelly_bot.channels.intake import Inbound, normalize
from dwelly_bot.context.collector import ContextCollector
from dwelly_bot.execution.contracts import ExecutionResult, Executor
from dwelly_bot.experiments.journal import Journal
from dwelly_bot.storage import file_hash, save_json


class PlanningComponent[PlanT: BaseModel](Protocol):
    async def plan(self, context: str) -> PlanT: ...


class ProductionPipeline[PlanT: BaseModel]:
    def __init__(
        self,
        collector: ContextCollector,
        planner: PlanningComponent[PlanT],
        executor: Executor[PlanT],
    ) -> None:
        self.collector = collector
        self.planner = planner
        self.executor = executor

    async def run(
        self,
        event: Inbound,
        output: Path,
        *,
        dataset: dict[str, Any] | None = None,
        is_active: Callable[[], bool] | None = None,
    ) -> ExecutionResult:
        """Create a new immutable capture; channel replies are executed plan actions."""
        output.mkdir(parents=True, exist_ok=False)
        journal = Journal(output / "events.jsonl")
        try:
            if dataset is not None:
                save_json(output / "dataset.json", dataset)
            save_json(output / "input.json", event.model_dump(mode="json"))
            with journal.record(
                "normalize", {"event_id": event.event_id}, kind="intake", read_only=True
            ) as entry:
                trigger = normalize(event)
                save_json(output / "trigger.json", trigger.model_dump(mode="json"))
                journal.returned(entry, trigger.model_dump(mode="json"))
            if is_active is not None and not is_active():
                raise ValueError("Session closed before collection")
            with journal.record(
                "collect", {"scope_id": trigger.scope_id}, kind="context", read_only=True
            ) as entry:
                context = await self.collector.collect(
                    trigger, capabilities=self.executor.capabilities, journal=journal
                )
                context.write(output / "context.md")
                save_json(output / "context.json", context.model_dump(mode="json"))
                journal.returned(
                    entry,
                    {
                        "context_sha256": file_hash(output / "context.md"),
                        "warnings": list(context.warnings),
                    },
                )
            if is_active is not None and not is_active():
                raise ValueError("Session closed before planning")
            with journal.record(
                "plan",
                {"context_sha256": file_hash(output / "context.md")},
                kind="planning",
                read_only=True,
            ) as entry:
                plan = await self.planner.plan(context.text)
                save_json(output / "plan.json", plan.model_dump(mode="json"))
                journal.returned(entry, plan.model_dump(mode="json"))
            if is_active is not None and not is_active():
                raise ValueError("Session closed before execution")
            result = await self.executor.execute(trigger, plan, journal)
            save_json(output / "result.json", result.model_dump(mode="json"))
            return result
        except BaseException as exc:
            save_json(
                output / "failure.json",
                {
                    "event_id": event.event_id,
                    "error_type": type(exc).__name__,
                    "status": "incomplete",
                },
            )
            raise
        finally:
            journal.close()
