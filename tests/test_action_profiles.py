from pathlib import Path

import pytest
from test_plan_execution import trigger

from dwelly_bot.execution import MockExecutor
from dwelly_bot.experiments.journal import Journal
from dwelly_bot.planning import Plan
from dwelly_bot.planning.catalog import ActionProfile
from dwelly_bot.planning.contracts import Calculate, ReplyToTrigger


async def test_calculation_result_flows_into_reply_and_replays(tmp_path: Path) -> None:
    plan = Plan(
        decision="Report total",
        disposition="respond",
        rationale="Given invoice amounts",
        actions=(
            Calculate(
                id="total", expression="125.50 + 24.50", rounding="cents", basis="Two invoices"
            ),
            ReplyToTrigger(id="reply", message="Total: {{total.value}}"),
        ),
    )
    executor = MockExecutor()
    journal = Journal(tmp_path / "journal.jsonl")
    try:
        result = await executor.execute(trigger("email"), plan, journal)
        repeated = await executor.execute(trigger("email"), plan, journal)
    finally:
        journal.close()
    assert result.receipts[0].status == "computed"
    assert result.receipts[1].parameters["message"] == "Total: 150.00"
    assert repeated.receipts[1].parameters == result.receipts[1].parameters
    assert len(executor.effects) == 1


def test_profiles_and_forward_references_are_rejected_before_execution() -> None:
    with pytest.raises(ValueError, match="Proposal-only"):
        MockExecutor(profile=ActionProfile.load("contest"))
    plan = Plan(
        decision="No",
        disposition="respond",
        rationale="No",
        actions=(ReplyToTrigger(id="reply", message="{{missing.value}}"),),
    )
    with pytest.raises(ValueError, match="reference"):
        ActionProfile.load().validate_plan(plan)
    assert len(ActionProfile.load().catalog()["actions"]) == 6  # type: ignore[arg-type]
