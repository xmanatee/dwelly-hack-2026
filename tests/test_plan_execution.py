from datetime import UTC, datetime
from pathlib import Path

import pytest
from pydantic import ValidationError

from dwelly_bot.channels.intake import CallInput, EmailInput, TicketInput, Trigger, normalize
from dwelly_bot.execution.mock import MockExecutor
from dwelly_bot.experiments.journal import Journal
from dwelly_bot.planning import HumanReviewPlanner, Plan
from dwelly_bot.planning.contracts import (
    CallCustomer,
    Handoff,
    ReplyToTrigger,
    SendEmail,
    UpdateTicket,
)


def trigger(channel: str, *, active: bool = True) -> Trigger:
    common = dict(
        event_id="event",
        scope_id="case",
        received_at=datetime(2026, 10, 10, tzinfo=UTC),
        text="Help",
    )
    if channel == "email":
        return normalize(
            EmailInput.model_validate({**common, "sender": "a@example.test", "thread_id": "thread"})
        )
    if channel == "call":
        return normalize(
            CallInput.model_validate(
                {**common, "caller": "+44000", "session_id": "session", "active": active}
            )
        )
    return normalize(TicketInput.model_validate({**common, "ticket_id": "ticket"}))


@pytest.mark.parametrize(
    ("channel", "operation"),
    [("email", "email_reply"), ("call", "speak_in_call"), ("ticket", "ticket_comment")],
)
async def test_stub_and_reply_route_with_duplicate_delivery(
    tmp_path: Path, channel: str, operation: str
) -> None:
    plan = await HumanReviewPlanner().plan("Prepared context")
    executor = MockExecutor()
    journal = Journal(tmp_path / "events.jsonl")
    try:
        first = await executor.execute(trigger(channel), plan, journal)
        replay = await executor.execute(trigger(channel), plan, journal)
    finally:
        journal.close()
    assert [r.operation for r in first.receipts] == ["handoff", operation]
    assert all(r.status == "simulated" for r in first.receipts)
    assert all(r.replayed for r in replay.receipts)
    assert len(executor.effects) == 2
    assert executor.effects[-1].parameters["message"] == first.receipts[-1].parameters["message"]
    assert replay.receipts[-1].parameters == first.receipts[-1].parameters


async def test_closed_call_fails_without_implicit_outbound_call(tmp_path: Path) -> None:
    executor = MockExecutor()
    plan = await HumanReviewPlanner().plan("context")
    journal = Journal(tmp_path / "events.jsonl")
    try:
        result = await executor.execute(trigger("call", active=False), plan, journal)
    finally:
        journal.close()
    assert result.status == "failed"
    assert result.receipts[-1].operation == "speak_in_call"
    assert [r.operation for r in executor.effects] == ["handoff"]


async def test_handoff_failure_prevents_success_message(tmp_path: Path) -> None:
    executor = MockExecutor(fail_actions=frozenset({"review"}))
    journal = Journal(tmp_path / "events.jsonl")
    try:
        result = await executor.execute(
            trigger("ticket"), await HumanReviewPlanner().plan("context"), journal
        )
    finally:
        journal.close()
    assert [r.status for r in result.receipts] == ["failed", "skipped"]
    assert not executor.effects


async def test_changed_action_rejected_and_categories_remain_distinct(tmp_path: Path) -> None:
    plan = Plan(
        decision="Demo",
        disposition="act",
        rationale="Test only",
        actions=(
            SendEmail(id="email", recipient="a@example.test", subject="Review", message="Hello"),
            CallCustomer(id="call", phone="+44000", message="Question"),
            UpdateTicket(id="ticket", ticket_id="t", status="pending", note="Waiting"),
        ),
    )
    executor = MockExecutor()
    journal = Journal(tmp_path / "events.jsonl")
    try:
        result = await executor.execute(trigger("ticket"), plan, journal)
        changed = Plan(
            decision="Demo",
            disposition="act",
            rationale="Test only",
            actions=(ReplyToTrigger(id="email", message="different operation"),),
        )
        conflict = await executor.execute(trigger("ticket"), changed, journal)
    finally:
        journal.close()
    assert [r.operation for r in result.receipts] == [
        "send_email",
        "call_customer",
        "update_ticket",
    ]
    assert conflict.status == "failed"
    assert len(executor.effects) == 3


def test_plan_rejects_unknown_operations_and_duplicate_ids() -> None:
    with pytest.raises(ValidationError):
        Plan.model_validate(
            dict(
                decision="No",
                disposition="act",
                rationale="No",
                actions=[dict(kind="execute_python", id="a", code="...")],
            )
        )
    with pytest.raises(ValidationError):
        Plan(
            decision="No",
            disposition="human_review",
            rationale="No",
            actions=(
                Handoff(id="a", queue="support", reason="reason"),
                ReplyToTrigger(id="a", message="message"),
            ),
        )
