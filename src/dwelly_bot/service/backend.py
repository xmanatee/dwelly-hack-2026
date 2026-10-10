"""Transport composition; all collection/planning/execution stays in the common harness."""

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from dwelly_bot.channels.intake import Inbound
from dwelly_bot.context.collector import ContextQuery, ContextRecord, ContextSource, SourceResult
from dwelly_bot.harness.local import run_local_pipeline
from dwelly_bot.planning import HumanReviewPlanner
from dwelly_bot.service.store import SessionStore
from dwelly_bot.storage import fingerprint


class SessionHistory:
    name = "session-customer-messages"

    def __init__(self, store: SessionStore, session: str, scope: str) -> None:
        self.store, self.session, self.scope = store, session, scope

    async def lookup(self, query: ContextQuery) -> SourceResult:
        if query.scope_id != self.scope:
            return SourceResult()
        rows = self.store.history(self.session)
        original = self.store.binding(self.session)
        records = (
            ContextRecord(
                id="bound-event",
                scope_id=self.scope,
                available_at=original.received_at,
                kind="event",
                source=self.name,
                text="Original inbound case message (not identity verification):\n" + original.text,
            ),
        )
        return SourceResult(
            records=records
            + tuple(
                ContextRecord(
                    id="turn-" + r["id"],
                    scope_id=self.scope,
                    available_at=datetime.fromtimestamp(r["started"], UTC),
                    kind="event",
                    source=self.name,
                    text="Prior customer message (assertion, not verified bank state):\n"
                    + r["text"],
                )
                for r in rows
            ),
            warnings=(
                "Session history includes at most the last 20 completed requests; generated plans are not bank evidence.",
            ),
        )


class PipelineBackend:
    def __init__(
        self,
        store: SessionStore,
        sources: tuple[ContextSource, ...],
        output: Path,
        *,
        planner_config: Path | None = None,
        context_config: Path | None = None,
        dataset: dict[str, Any] | None = None,
    ) -> None:
        self.store, self.sources, self.output = store, sources, output
        self.planner_config, self.context_config, self.dataset = (
            planner_config,
            context_config,
            dataset,
        )

    async def __call__(self, event: Inbound, session: str, request: str) -> dict[str, Any]:
        capture = self.output / fingerprint([session, request])
        result = await run_local_pipeline(
            event,
            (*self.sources, SessionHistory(self.store, session, event.scope_id)),
            HumanReviewPlanner(),
            capture,
            state=self.output.parent / "action-receipts.sqlite",
            planner_config=self.planner_config,
            context_config=self.context_config,
            dataset=self.dataset,
            is_active=lambda: self.store.active(session),
        )
        if result.status == "failed":
            raise RuntimeError("Execution failed; consult the local capture")
        return {
            "status": "complete",
            "execution": "mock",
            "external_effects": False,
            "notice": "These are decisions and simulated operations, not completed bank actions. Do not claim a transfer, handoff or update occurred.",
            "plan": json.loads((capture / "plan.json").read_text()),
            "result": result.model_dump(mode="json"),
        }
