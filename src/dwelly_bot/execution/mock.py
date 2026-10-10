"""Categorized offline operations with local replay protection and explicit simulation.

The one optional live path: a reply to an open voice call is queued as speech in that call.
"""

import json
from pathlib import Path

from pydantic_ai import ModelRetry

from dwelly_bot.channels.intake import CallRoute, EmailRoute, Trigger
from dwelly_bot.channels.live_call import LiveCalls
from dwelly_bot.execution.contracts import ActionReceipt, ExecutionResult
from dwelly_bot.execution.receipts import ReceiptStore
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
    """Local journal/receipts and arithmetic; with `live_calls`, replies to an open call are spoken."""

    def __init__(
        self,
        *,
        fail_actions: frozenset[str] = frozenset(),
        profile: ActionProfile | None = None,
        state_path: Path | None = None,
        live_calls: LiveCalls | None = None,
    ) -> None:
        self.fail_actions = fail_actions
        self.inactive_calls: set[str] = set()
        self.effects: list[ActionReceipt] = []
        self.store = ReceiptStore(state_path)
        self.live_calls = live_calls
        self.profile = profile or ActionProfile.load()
        if self.profile.execution != "mock":
            raise ValueError("Proposal-only profiles cannot be executed")

    @property
    def capabilities(self) -> str:
        scope = (
            "LIVE CALL REPLY: reply_to_trigger is spoken in the caller's open voice session. "
            "Every other action is MOCK ONLY: no messages, calls or handoffs occur.\n"
            if self.live_calls is not None
            else "MOCK ONLY: no messages, calls or handoffs occur.\n"
        )
        return scope + json.dumps(self.profile.catalog(), ensure_ascii=False)

    def _speak(self, action: Action, session_id: str, message: str) -> ActionReceipt:
        assert self.live_calls is not None
        if action.id in self.fail_actions or not self.live_calls.say(session_id, message):
            return ActionReceipt(
                action_id=action.id,
                status="failed",
                operation="speak_in_call",
                target=session_id,
                detail="Injected failure."
                if action.id in self.fail_actions
                else "Voice session is closed; no automatic callback was attempted.",
            )
        return ActionReceipt(
            action_id=action.id,
            status="sent",
            operation="speak_in_call",
            target=session_id,
            detail="Queued as speech in the open voice session; the voice transport returns it to the caller.",
        )

    def _simulate(
        self, trigger: Trigger, action: Action, parameters: dict[str, str]
    ) -> ActionReceipt:
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
                if self.live_calls is not None:
                    return self._speak(action, route.session_id, parameters["message"])
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
                else:
                    parameters = action.model_dump(exclude={"id", "kind"})
                    for field in ("message", "note", "subject"):
                        if field in parameters:
                            parameters[field] = render_message(parameters[field], results)

                    def invoke(
                        action: Action = action, parameters: dict[str, str] = parameters
                    ) -> ActionReceipt:
                        return self._simulate(trigger, action, parameters).model_copy(
                            update={"parameters": parameters}
                        )

                    try:
                        receipt = self.store.apply(key, digest, invoke)
                    except ValueError as exc:
                        receipt = ActionReceipt(
                            action_id=action.id,
                            status="failed",
                            operation=action.kind,
                            target="",
                            detail=str(exc),
                        )
                    if receipt.status in {"simulated", "sent"} and not receipt.replayed:
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
