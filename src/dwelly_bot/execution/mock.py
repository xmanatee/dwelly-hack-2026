"""Categorized offline operations with local replay protection and explicit simulation."""

import json

from pydantic_ai import ModelRetry

from dwelly_bot.channels.intake import CallRoute, EmailRoute, Trigger
from dwelly_bot.execution.contracts import ActionReceipt, ExecutionResult
from dwelly_bot.experiments.journal import Journal
from dwelly_bot.planning.catalog import ActionProfile, render_message
from dwelly_bot.planning.contracts import (
    Action,
    Calculate,
    CallCustomer,
    Handoff,
    Plan,
    ReplyToTrigger,
    SendEmail,
)
from dwelly_bot.storage import fingerprint
from dwelly_bot.tools.arithmetic import calculate


class MockExecutor:
    """No I/O except the shared journal. Replay cache lasts for this instance only."""

    def __init__(
        self, *, fail_actions: frozenset[str] = frozenset(), profile: ActionProfile | None = None
    ) -> None:
        self.fail_actions = fail_actions
        self.inactive_calls: set[str] = set()
        self.effects: list[ActionReceipt] = []
        self._receipts: dict[str, tuple[str, ActionReceipt]] = {}
        self.profile = profile or ActionProfile.load()
        if self.profile.execution != "mock":
            raise ValueError("Proposal-only profiles cannot be executed")

    @property
    def capabilities(self) -> str:
        return "MOCK ONLY: no messages, calls or handoffs occur.\n" + json.dumps(
            self.profile.catalog(), ensure_ascii=False
        )

    def _simulate(self, trigger: Trigger, action: Action) -> ActionReceipt:
        operation: str = action.kind
        target = trigger.scope_id
        if isinstance(action, Calculate):
            try:
                value = calculate(action.expression, action.rounding)
                return ActionReceipt(
                    action_id=action.id,
                    status="computed",
                    operation=operation,
                    target="local",
                    detail="Local arithmetic only; no financial operation.",
                    outputs=value,
                )
            except ModelRetry as exc:
                return ActionReceipt(
                    action_id=action.id,
                    status="failed",
                    operation=operation,
                    target="local",
                    detail=str(exc),
                )
        if isinstance(action, ReplyToTrigger):
            route = trigger.reply_route
            if isinstance(route, EmailRoute):
                operation, target = "email_reply", f"{route.recipient} / {route.thread_id}"
            elif isinstance(route, CallRoute):
                operation, target = "speak_in_call", route.session_id
                if not route.active or route.session_id in self.inactive_calls:
                    return ActionReceipt(
                        action_id=action.id,
                        status="failed",
                        operation=operation,
                        target=target,
                        detail="Call is no longer active; no automatic callback was attempted.",
                    )
            else:
                operation, target = "ticket_comment", route.ticket_id
        elif isinstance(action, SendEmail):
            target = action.recipient
        elif isinstance(action, CallCustomer):
            target = action.phone
        elif isinstance(action, Handoff):
            target = action.queue
        else:
            target = action.ticket_id
        failed = action.id in self.fail_actions
        return ActionReceipt(
            action_id=action.id,
            status="failed" if failed else "simulated",
            operation=operation,
            target=target,
            detail="Injected mock failure."
            if failed
            else "Simulated only; no external effect or delivery confirmation.",
        )

    async def execute(self, trigger: Trigger, plan: Plan, journal: Journal) -> ExecutionResult:
        self.profile.validate_plan(plan)
        receipts: list[ActionReceipt] = []
        results: dict[str, str] = {}
        blocked = False
        for action in plan.actions:
            key = fingerprint([trigger.scope_id, trigger.event_id, action.id])
            digest = fingerprint(
                {
                    "trigger": trigger.model_dump(mode="json"),
                    "action": action.model_dump(mode="json"),
                }
            )
            with journal.record(
                action.kind,
                {
                    "trigger": trigger.model_dump(mode="json"),
                    "action": action.model_dump(mode="json"),
                    "idempotency_key": key,
                },
                kind="mock_action",
                read_only=True,
            ) as event:
                if blocked:
                    receipt = ActionReceipt(
                        action_id=action.id,
                        status="skipped",
                        operation=action.kind,
                        target="",
                        detail="Earlier action failed; no subsequent operation attempted.",
                    )
                elif key in self._receipts:
                    old_digest, previous = self._receipts[key]
                    if old_digest != digest:
                        receipt = ActionReceipt(
                            action_id=action.id,
                            status="failed",
                            operation=action.kind,
                            target="",
                            detail="Idempotency conflict: event/action ID reused with changed input.",
                        )
                    else:
                        receipt = previous.model_copy(update={"replayed": True})
                else:
                    parameters = action.model_dump(exclude={"id", "kind"})
                    for field in ("message", "note", "subject"):
                        if field in parameters:
                            parameters[field] = render_message(parameters[field], results)
                    receipt = self._simulate(trigger, action).model_copy(
                        update={"parameters": parameters}
                    )
                    self._receipts[key] = (digest, receipt)
                    if receipt.status == "simulated":
                        self.effects.append(receipt)
                if receipt.status == "computed":
                    results[action.id + ".value"] = receipt.outputs["value"]
                journal.returned(event, receipt.model_dump(mode="json"))
            blocked = blocked or receipt.status == "failed"
            receipts.append(receipt)
        return ExecutionResult(
            event_id=trigger.event_id,
            status="failed" if blocked else "simulated" if receipts else "empty",
            disposition=plan.disposition,
            receipts=tuple(receipts),
        )
