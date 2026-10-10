"""Knowledge routing, repair, no-tool boundary and cumulative usage limits."""

import json
from pathlib import Path

import pytest
from pydantic import ValidationError
from pydantic_ai.messages import ModelMessage, ModelResponse, ToolCallPart
from pydantic_ai.models.function import AgentInfo, FunctionModel

from dwelly_bot.contracts import PlannerConfig, RunConfig
from dwelly_bot.experiments.journal import Journal, recover_events
from dwelly_bot.harness.runtime import CaseRuntime
from dwelly_bot.planner import PlanInput
from dwelly_bot.planner.planner import plan_case
from dwelly_bot.planner.skills import Skill, catalog, select_skills
from dwelly_bot.resources import text

SOURCE = PlanInput(
    case_id="mixed",
    decision_time="2026-01-01",
    request="My partner watches my phone. I need to stop a Direct Debit safely.",
)
PLAN = {
    "intent": "safe-help",
    "summary": "Refer safely",
    "identity_authority": "unclear",
    "safety_flags": ["financial_abuse"],
    "expected_disposition": "escalated",
    "steps": [
        {
            "id": "s1",
            "kind": "proposed_action",
            "action": "hold_or_decline",
            "instruction": "Hold unsafe disclosure",
            "rationale": {
                "explanation": "A partner monitors the phone",
                "evidence": ["request"],
                "criterion": "Avoid unsafe contact",
                "source": "general:safety",
            },
        },
        {
            "id": "s2",
            "kind": "proposed_action",
            "action": "refer_specialist",
            "instruction": "Agree safe contact",
            "rationale": {
                "explanation": "Specialist safe-contact handling is needed",
                "evidence": ["request"],
                "criterion": "Protect against disclosed coercive monitoring",
                "source": "general:safety",
            },
        },
    ],
}


def test_packaged_catalog_and_sources_are_complete() -> None:
    skills = catalog("banking")
    sources = json.loads(text("planner/skills/sources.json"))
    assert len(skills) == 11
    for skill in skills:
        body = text(skill.resource)
        assert f"name: {skill.id}" in body and skill.description in body
        assert len(body) < 5000
        for source in skill.sources:
            assert sources[source]["url"] in body
    with pytest.raises(ValidationError):
        Skill(id="../../private", description="bad", sources=[])
    with pytest.raises(ValueError, match="No skill catalog"):
        catalog("unknown")


async def test_only_selected_topics_plus_common_rules_reach_plan(journal: Journal) -> None:
    calls: list[str] = []

    def model(messages: list[ModelMessage], info: AgentInfo) -> ModelResponse:
        tool = info.output_tools[0].name
        calls.append(tool)
        assert not info.function_tools
        assert SOURCE.request in str(messages)
        if tool == "planner_skill_selection":
            assert "financial-abuse" in str(info.instructions)
            return ModelResponse(
                parts=[ToolCallPart(tool, {"skill_ids": ["financial-abuse", "scheduled-payments"]})]
            )
        prompt = str(info.instructions)
        assert "# Evidence and supplied context" in prompt
        assert "# Always-on triage" in prompt
        assert "# Financial Abuse" in prompt and "# Scheduled Payments" in prompt
        assert "# Bereavement Authority" not in prompt
        assert "# Business Authority" not in prompt
        return ModelResponse(parts=[ToolCallPart(tool, PLAN)])

    runtime = CaseRuntime(FunctionModel(model), RunConfig(), journal)
    result = await plan_case(runtime, SOURCE, PlannerConfig())
    assert result["status"] == "available"
    assert calls == ["planner_skill_selection", "case_plan"]
    selection = journal.events[0]["result"]
    assert set(selection["selected"]) == {"financial-abuse", "scheduled-payments"}
    assert all(len(item["sha256"]) == 64 for item in selection["resources"])
    assert [r["role"] for r in runtime.role_records] == ["planner", "planner"]
    recovered = recover_events(Path(journal.file.name))
    assert len(recovered) == 2 and all(e["status"] == "returned" for e in recovered)


@pytest.mark.parametrize("bad", [["../../private"], ["payments", "payments"], ["invented"]])
async def test_selection_is_repaired_before_loading(bad: list[str], journal: Journal) -> None:
    attempts = 0

    def model(messages: list[ModelMessage], info: AgentInfo) -> ModelResponse:
        nonlocal attempts
        attempts += 1
        return ModelResponse(
            parts=[
                ToolCallPart(
                    info.output_tools[0].name, {"skill_ids": bad if attempts == 1 else ["payments"]}
                )
            ]
        )

    runtime = CaseRuntime(FunctionModel(model), RunConfig(), journal)
    selected = await select_skills(runtime, SOURCE, PlannerConfig())
    assert attempts == 2
    assert [p for p, _ in selected] == ["planner/skills/payments/SKILL.md"]


async def test_no_topic_still_loads_safety_and_evidence(journal: Journal) -> None:
    def model(messages: list[ModelMessage], info: AgentInfo) -> ModelResponse:
        tool = info.output_tools[0].name
        if tool == "planner_skill_selection":
            return ModelResponse(parts=[ToolCallPart(tool, {"skill_ids": []})])
        assert "# Always-on triage" in str(info.instructions)
        assert "# Evidence and supplied context" in str(info.instructions)
        return ModelResponse(parts=[ToolCallPart(tool, PLAN)])

    runtime = CaseRuntime(FunctionModel(model), RunConfig(), journal)
    assert (await plan_case(runtime, SOURCE, PlannerConfig()))["status"] == "available"


async def test_selector_failure_is_not_silently_replaced(journal: Journal) -> None:
    def fail(messages: list[ModelMessage], info: AgentInfo) -> ModelResponse:
        raise RuntimeError("selector unavailable")

    runtime = CaseRuntime(FunctionModel(fail), RunConfig(), journal)
    result = await plan_case(runtime, SOURCE, PlannerConfig())
    assert result["status"] == "error" and "selector unavailable" in result["error"]
    assert journal.events[0]["status"] == "error"
    assert len(runtime.role_records) == 1


async def test_selection_and_plan_share_request_limit(journal: Journal) -> None:
    def model(messages: list[ModelMessage], info: AgentInfo) -> ModelResponse:
        assert info.output_tools[0].name == "planner_skill_selection"
        return ModelResponse(parts=[ToolCallPart("planner_skill_selection", {"skill_ids": []})])

    runtime = CaseRuntime(FunctionModel(model), RunConfig(max_requests=1), journal)
    result = await plan_case(runtime, SOURCE, PlannerConfig())
    assert result["status"] == "error" and "request_limit" in result["error"]


async def test_all_mode_skips_selection_call(journal: Journal) -> None:
    def model(messages: list[ModelMessage], info: AgentInfo) -> ModelResponse:
        assert info.output_tools[0].name == "case_plan"
        assert "# Business Authority" in str(info.instructions)
        return ModelResponse(parts=[ToolCallPart("case_plan", PLAN)])

    runtime = CaseRuntime(FunctionModel(model), RunConfig(), journal)
    assert (await plan_case(runtime, SOURCE, PlannerConfig(skill_selection="all")))[
        "status"
    ] == "available"
    assert len(runtime.role_records) == 1


async def test_topic_analysis_ignores_labels(tmp_path: Path) -> None:
    from dwelly_bot.analysis import AnalysisContext
    from dwelly_bot.analysis.planner_topics import build

    folder = tmp_path / "data/001"
    folder.mkdir(parents=True)
    (folder / "history.md").write_text("Customer asks about a transfer")
    (folder / "index.md").write_text("PRIVATE_EXPECTED_ANSWER")
    (folder.parent / "labels.json").write_text("PRIVATE_EXPECTED_ANSWER")
    ctx = AnalysisContext(folder.parent, tmp_path / "out", tmp_path / "cache")
    report = await build(ctx)
    assert "PRIVATE_EXPECTED_ANSWER" not in report.model_dump_json()
    assert report.blocks[0].data["Cases"] == 1
