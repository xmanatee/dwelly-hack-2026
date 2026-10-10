import json
from contextlib import nullcontext
from datetime import UTC, datetime
from pathlib import Path

import pytest
from pydantic_ai.messages import ModelMessage, ModelResponse, ToolCallPart
from pydantic_ai.models.function import AgentInfo, FunctionModel

from dwelly_bot.channels.intake import CallInput, normalize
from dwelly_bot.contracts import ModelProfile, RunConfig
from dwelly_bot.execution.decision import DecisionExecutor
from dwelly_bot.experiments.journal import Journal
from dwelly_bot.harness.local import run_local_pipeline
from dwelly_bot.planner.contracts import Plan, PlanStep, StepRationale
from dwelly_bot.planning import HumanReviewPlanner


def decision() -> Plan:
    return Plan(
        intent="status",
        summary="Ask for the missing reference",
        identity_authority="not_needed",
        expected_disposition="needs_info",
        steps=[
            PlanStep(
                id="s1",
                kind="proposed_action",
                action="ask_customer",
                instruction="Ask which payment reference the customer means.",
                rationale=StepRationale(
                    explanation="The payment is not identified.",
                    evidence=["request"],
                    criterion="Identify the requested operation",
                    source="general:evidence",
                ),
            )
        ],
    )


def call(active: bool = True) -> CallInput:
    return CallInput(
        event_id="e1",
        scope_id="case1",
        received_at=datetime(2026, 10, 10, tzinfo=UTC),
        text="Where is my transfer?",
        caller="+440000000",
        session_id="session1",
        active=active,
    )


async def test_local_uses_actual_shared_planner_and_retains_trace(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    calls: list[str] = []

    def model(messages: list[ModelMessage], info: AgentInfo) -> ModelResponse:
        name = info.output_tools[0].name
        calls.append(name)
        assert not info.function_tools
        assert "Where is my transfer" in str(messages)
        return ModelResponse(
            parts=[
                ToolCallPart(
                    name,
                    {"skill_ids": ["payments"]}
                    if name == "planner_skill_selection"
                    else decision().model_dump(mode="json"),
                )
            ]
        )

    monkeypatch.setattr(
        "dwelly_bot.planner.service.transport", lambda p: (nullcontext(FunctionModel(model)), p)
    )
    monkeypatch.setattr(
        "dwelly_bot.planner.service.ledger_path", lambda c: tmp_path / "ledger.json"
    )
    config = tmp_path / "config.json"
    config.write_text(
        RunConfig(
            **ModelProfile(
                provider="anthropic",
                model="test",
                input_price_per_million=1,
                output_price_per_million=1,
            ).model_dump()
        ).model_dump_json()
    )
    out = tmp_path / "run"
    result = await run_local_pipeline(
        call(),
        (),
        HumanReviewPlanner(),
        out,
        planner_config=config,
        state=tmp_path / "state.sqlite",
    )
    assert calls == ["planner_skill_selection", "case_plan"]
    assert result.receipts[0].operation == "ask_customer"
    assert "session1" in result.receipts[0].target
    assert Plan.model_validate_json((out / "plan.json").read_text()) == decision()
    trace = json.loads((out / "planner.jsonl").read_text().splitlines()[-1])
    assert len(trace["costs"]) == 2 and len(trace["roles"]) == 2


async def test_decision_replay_conflict_and_inactive_call(tmp_path: Path) -> None:
    executor = DecisionExecutor(tmp_path / "receipts.sqlite")
    journal = Journal(tmp_path / "journal.jsonl")
    try:
        first = await executor.execute(normalize(call()), decision(), journal)
        assert first.status == "simulated"
        replay = await DecisionExecutor(tmp_path / "receipts.sqlite").execute(
            normalize(call()), decision(), journal
        )
        assert replay.receipts[0].replayed
        changed = decision()
        changed.steps[0].instruction = "A different instruction"
        assert (await executor.execute(normalize(call()), changed, journal)).status == "failed"
        assert (
            await DecisionExecutor().execute(normalize(call(False)), decision(), journal)
        ).status == "failed"
        invalid = decision()
        invalid.steps[0].requires = ["s9"]
        with pytest.raises(ValueError, match="unordered"):
            await executor.execute(normalize(call()), invalid, journal)
    finally:
        journal.close()
