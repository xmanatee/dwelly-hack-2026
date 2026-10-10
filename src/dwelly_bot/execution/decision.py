"""Execute the canonical case-plan contract in explicit local simulation."""

from pathlib import Path

from dwelly_bot.channels.intake import CallRoute, Trigger
from dwelly_bot.execution.contracts import ActionReceipt, ExecutionResult
from dwelly_bot.execution.receipts import ReceiptStore
from dwelly_bot.experiments.journal import Journal
from dwelly_bot.planner.contracts import Plan, PlanStep
from dwelly_bot.planner.planner import playbook
from dwelly_bot.storage import fingerprint


class DecisionExecutor:
    """Preserve every ordered operation and ground; no external effects or invented replies."""

    def __init__(self, state_path: Path | None = None) -> None:
        self.store = ReceiptStore(state_path)

    @property
    def capabilities(self) -> str:
        _, vocabulary = playbook("banking")
        return (
            "MOCK ONLY: no external effects. Available decision actions:\n"
            + vocabulary.model_dump_json()
        )

    async def execute(self, trigger: Trigger, plan: Plan, journal: Journal) -> ExecutionResult:
        _, vocabulary = playbook("banking")
        seen: set[str] = set()
        # Validate the whole plan before recording any simulated effect.
        for step in plan.steps:
            if (
                step.id in seen
                or set(step.requires) - seen
                or step.condition is not None
                or step.kind != "proposed_action"
                or step.action not in vocabulary.actions
            ):
                raise ValueError("Unsupported, conditional or unordered decision step")
            seen.add(step.id)
        receipts: list[ActionReceipt] = []
        blocked = False
        for step in plan.steps:
            key = fingerprint(["decision", trigger.scope_id, trigger.event_id, step.id])
            digest = fingerprint([trigger.model_dump(mode="json"), step.model_dump(mode="json")])
            target = step.target or trigger.scope_id
            if step.action in {"reply_to_customer", "ask_customer"}:
                target = trigger.reply_route.model_dump_json()
            failed = (
                isinstance(trigger.reply_route, CallRoute)
                and not trigger.reply_route.active
                and step.action in {"reply_to_customer", "ask_customer"}
            )
            with journal.record(
                step.action,
                {"step": step.model_dump(mode="json"), "idempotency_key": key},
                kind="mock_decision",
                read_only=True,
            ) as entry:

                def invoke(
                    step: PlanStep = step, target: str = target, failed: bool = failed
                ) -> ActionReceipt:
                    return ActionReceipt(
                        action_id=step.id,
                        operation=step.action,
                        target=target,
                        status="failed" if failed else "simulated",
                        detail="Call is inactive; no callback attempted."
                        if failed
                        else "Simulated decision operation; no external effect.",
                        parameters={"instruction": step.instruction},
                    )

                if blocked:
                    receipt = ActionReceipt(
                        action_id=step.id,
                        operation=step.action,
                        target=target,
                        status="skipped",
                        detail="Earlier operation failed.",
                    )
                else:
                    try:
                        receipt = self.store.apply(key, digest, invoke)
                    except ValueError as exc:
                        receipt = ActionReceipt(
                            action_id=step.id,
                            operation=step.action,
                            target=target,
                            status="failed",
                            detail=str(exc),
                        )
                blocked |= receipt.status == "failed"
                receipts.append(receipt)
                journal.returned(entry, receipt.model_dump(mode="json"))
        return ExecutionResult(
            event_id=trigger.event_id,
            status="failed" if blocked else "simulated",
            disposition=plan.expected_disposition,
            receipts=tuple(receipts),
        )
