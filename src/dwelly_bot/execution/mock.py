"""Categorized offline operations with local replay protection and explicit simulation."""

from dwelly_bot.channels.intake import CallRoute, EmailRoute, Trigger
from dwelly_bot.execution.contracts import ActionReceipt, ExecutionResult
from dwelly_bot.experiments.journal import Journal
from dwelly_bot.planning.contracts import (
    ACTION_CATALOG,
    Action,
    CallCustomer,
    Handoff,
    Plan,
    ReplyToTrigger,
    SendEmail,
)
from dwelly_bot.storage import fingerprint


class MockExecutor:
    """No I/O except the shared journal. Replay cache lasts for this instance only."""

    def __init__(self, *, fail_actions: frozenset[str] = frozenset()) -> None:
        self.fail_actions = fail_actions
        self.inactive_calls: set[str] = set()
        self.effects: list[ActionReceipt] = []
        self._receipts: dict[str, tuple[str, ActionReceipt]] = {}

    @property
    def capabilities(self) -> str:
        return (
            "MOCK ONLY: no messages, calls or handoffs occur.\n"
            + "\n".join(f"- {kind}: {description}" for kind, description in ACTION_CATALOG.items())
            + "\nAvailable handoff queue: human-support."
        )

    def _simulate(self, trigger: Trigger, action: Action) -> ActionReceipt:
        operation: str = action.kind
        target = trigger.scope_id
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
        receipts: list[ActionReceipt] = []
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
                    receipt = self._simulate(trigger, action).model_copy(
                        update={"parameters": action.model_dump(exclude={"id", "kind"})}
                    )
                    self._receipts[key] = (digest, receipt)
                    if receipt.status == "simulated":
                        self.effects.append(receipt)
                receipt = receipt.model_copy(
                    update={"parameters": action.model_dump(exclude={"id", "kind"})}
                )
                journal.returned(event, receipt.model_dump(mode="json"))
            blocked = blocked or receipt.status == "failed"
            receipts.append(receipt)
        return ExecutionResult(
            event_id=trigger.event_id,
            status="failed" if blocked else "simulated" if receipts else "empty",
            disposition=plan.disposition,
            receipts=tuple(receipts),
        )
