import json
from datetime import UTC, datetime
from pathlib import Path

import pytest

from dwelly_bot.channels.intake import TicketInput
from dwelly_bot.cli import main
from dwelly_bot.context.collector import ContextCollector
from dwelly_bot.execution import MockExecutor
from dwelly_bot.harness.production import ProductionPipeline
from dwelly_bot.planning import HumanReviewPlanner, Plan

ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.parametrize(
    ("channel", "operation"),
    [("email", "email_reply"), ("call", "speak_in_call"), ("ticket", "ticket_comment")],
)
def test_cli_vertical_slice(tmp_path: Path, channel: str, operation: str) -> None:
    output = tmp_path / channel
    args = [
        "demo",
        "--input",
        str(ROOT / f"examples/production/{channel}.json"),
        "--records",
        str(ROOT / "examples/production/records.json"),
        "--output",
        str(output),
    ]
    assert main(args) == 0
    context = (output / "context.md").read_text()
    assert "No bank receipt confirmation is available" in context
    assert "FUTURE RECORD" not in context and "UNRELATED RECORD" not in context
    plan = Plan.model_validate_json((output / "plan.json").read_text())
    assert plan.disposition == "human_review"
    result = json.loads((output / "result.json").read_text())
    assert result["mode"] == "mock"
    assert result["receipts"][-1]["operation"] == operation
    events = [json.loads(line) for line in (output / "events.jsonl").read_text().splitlines()]
    assert all(e["status"] == "returned" for e in events if "ended_at" in e)
    original = (output / "result.json").read_bytes()
    with pytest.raises(SystemExit) as error:
        main(args)
    assert error.value.code == 2
    assert (output / "result.json").read_bytes() == original


async def test_planner_gets_exact_saved_text_and_failure_keeps_context(tmp_path: Path) -> None:
    output = tmp_path / "capture"

    class BrokenPlanner:
        async def plan(self, context: str) -> Plan:
            assert context == (output / "context.md").read_text()
            raise RuntimeError("planner unavailable")

    pipeline = ProductionPipeline(ContextCollector(()), BrokenPlanner(), MockExecutor())
    event = TicketInput(
        event_id="1",
        scope_id="s",
        received_at=datetime(2026, 10, 10, tzinfo=UTC),
        text="Need help",
        ticket_id="t",
    )
    with pytest.raises(RuntimeError, match="planner unavailable"):
        await pipeline.run(event, output)
    assert (output / "context.md").exists()
    assert not (output / "result.json").exists()
    assert json.loads((output / "failure.json").read_text())["error_type"] == "RuntimeError"
    assert json.loads((output / "events.jsonl").read_text().splitlines()[-1])["status"] == "error"


async def test_no_extra_delivery_after_plan_execution(tmp_path: Path) -> None:
    executor = MockExecutor()
    pipeline = ProductionPipeline(ContextCollector(()), HumanReviewPlanner(), executor)
    event = TicketInput(
        event_id="1",
        scope_id="s",
        received_at=datetime(2026, 10, 10, tzinfo=UTC),
        text="Help",
        ticket_id="t",
    )
    await pipeline.run(event, tmp_path / "first")
    result = await pipeline.run(event, tmp_path / "replayed")
    assert len(executor.effects) == 2
    assert all(receipt.replayed for receipt in result.receipts)


def test_calculation_cli_survives_restart_and_exports_catalog(tmp_path: Path) -> None:
    args = [
        "demo",
        "--input",
        str(ROOT / "examples/production/calculation.json"),
        "--plan",
        str(ROOT / "examples/production/calculation-plan.json"),
        "--state",
        str(tmp_path / "state.sqlite"),
    ]
    assert main([*args, "--output", str(tmp_path / "first")]) == 0
    assert main([*args, "--output", str(tmp_path / "second")]) == 0
    result = json.loads((tmp_path / "second/result.json").read_text())
    assert all(r["replayed"] for r in result["receipts"])
    assert (
        result["receipts"][1]["parameters"]["message"] == "Total of the supplied amounts: 150.00."
    )
    assert (
        main(["actions", "--profile", "contest", "--output", str(tmp_path / "catalog.json")]) == 0
    )
    assert json.loads((tmp_path / "catalog.json").read_text())["profile"]["execution"] == "proposal"
