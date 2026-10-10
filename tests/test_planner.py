"""Planner: decision-point input, code-checked plans, repair, advisory solver use and isolation."""

import json
from pathlib import Path
from typing import Any

import pytest
from pydantic_ai.messages import ModelMessage, ModelResponse, ToolCallPart
from pydantic_ai.models.function import AgentInfo, FunctionModel

from dwelly_bot.adapters.banking import BankingSession
from dwelly_bot.context.documents import Documents
from dwelly_bot.contracts import AgentCase, PlannerConfig, RunConfig
from dwelly_bot.experiments.journal import Journal
from dwelly_bot.harness.runtime import CaseRuntime
from dwelly_bot.planner.cli import main as plan_cli
from dwelly_bot.planner.context import parse_events
from dwelly_bot.planner.contracts import Plan
from dwelly_bot.planner.planner import plan_case, playbook
from dwelly_bot.planner.validate import check_plan

HISTORY = """## 2025-07-27 09:00:00 UTC — event 001

- **Channel:** Secure portal
- **From:** Harrow & Vale Bank plc
- **To:** Leona Mercer

Transfer status: sent.

## 2025-07-27 09:47:00 UTC — event 002

- **Channel:** Verified call
- **From:** Leona Mercer
- **To:** H&V service agent

My identity checks are complete.
Please register a return request.
"""

PLAN: dict[str, Any] = {
    "intent": "payments.stop_return",
    "summary": "Register a return request for a verified misdirected transfer.",
    "facts": [{"claim": "Identity checks complete on a verified call", "evidence": ["event-002"]}],
    "missing": ["Receiving bank response"],
    "identity_authority": "established",
    "safety_flags": [],
    "steps": [
        {
            "id": "s1",
            "kind": "solver_tool",
            "action": "read_document",
            "instruction": "Read the history",
            "rationale": {
                "explanation": "Use the supplied transfer evidence",
                "evidence": ["event-001"],
                "criterion": "Use recorded transaction facts",
                "source": "general:evidence",
            },
            "arguments": {"document": "history.md"},
        },
        {
            "id": "s2",
            "kind": "proposed_action",
            "action": "request_team_action",
            "instruction": "Register the return request",
            "rationale": {
                "explanation": "The verified customer requested a return",
                "evidence": ["event-002"],
                "criterion": "Initiate an authorised customer request",
                "source": "general:planner",
            },
            "target": "payment team",
            "requires": ["s1"],
        },
        {
            "id": "s3",
            "kind": "proposed_action",
            "action": "reply_to_customer",
            "instruction": "Report registration only",
            "rationale": {
                "explanation": "Do not promise funds back",
                "evidence": ["event-002"],
                "criterion": "A request is not proof of recovery",
                "source": "general:evidence",
            },
            "requires": ["s2"],
        },
    ],
    "escalate_if": [],
    "must_state": ["Registration does not confirm a return"],
    "must_not": ["Promise the money back"],
    "expected_disposition": "escalated",
}


def session(tmp_path: Path) -> BankingSession:
    folder = tmp_path / "banking-005"
    (folder / "attachments").mkdir(parents=True)
    (folder / "request.md").write_text("Please register a return request.\n")
    (folder / "history.md").write_text(HISTORY)
    (folder / "attachments" / "note.md").write_text("Attachment text\n")
    case = AgentCase(
        id="banking-005",
        dataset="dwelly-banking",
        title="Banking case 005",
        input={
            "request": "Please register a return request.",
            "decision_time": "2025-07-27 09:47:00 UTC",
            "visible_events": 2,
            "task": "Give the next supported response.",
        },
    )
    return BankingSession(case, Documents(folder))


def reply(info: AgentInfo, payload: dict[str, Any]) -> ModelResponse:
    return ModelResponse(parts=[ToolCallPart(info.output_tools[0].name, payload)])


ANSWER = {
    "answer": "Proposed",
    "public_rationale": "history.md:L7",
    "agent_disposition": "escalated",
}


def test_events_documents_and_tools_come_from_decision_point_evidence(tmp_path: Path) -> None:
    source = session(tmp_path).plan_input(RunConfig(disabled_tools=["calculate"]))
    assert [e.id for e in source.events] == ["event-001", "event-002"]
    assert source.events[1].sender == "Leona Mercer"
    assert (
        source.events[1].text
        == "My identity checks are complete.\nPlease register a return request."
    )
    assert [d.name for d in source.documents] == ["attachments/note.md"]
    assert {t.name for t in source.solver_tools} == {
        "list_documents",
        "read_document",
        "search_documents",
    }
    assert source.evidence_ids() == {"request", "event-001", "event-002", "attachments/note.md"}
    anchored = HISTORY.replace("## 2025-07-27 09:47", '<a id="event-002"></a>\n## 2025-07-27 09:47')
    assert parse_events(anchored)[0].text == "Transfer status: sent."


@pytest.mark.parametrize(
    ("change", "message"),
    [
        (lambda p: p["steps"][0].update(action="send_email"), "not a solver tool"),
        (lambda p: p["steps"][0].update(arguments={"path": "x"}), "unknown arguments"),
        (lambda p: p["steps"][1].update(action="refund_now"), "not a playbook action"),
        (lambda p: p["steps"][1].update(requires=["s3"]), "do not come earlier"),
        (lambda p: p["facts"][0].update(evidence=["event-009"]), "unknown evidence"),
        (lambda p: p.update(safety_flags=["scam_in_progress"]), "requires actions"),
        (lambda p: p.update(safety_flags=["made_up"]), "Unknown safety flag"),
        (lambda p: p.update(identity_authority="unclear"), "before identity/authority"),
    ],
)
def test_code_checks_reject_ungrounded_or_unsafe_plans(
    tmp_path: Path, change: Any, message: str
) -> None:
    source = session(tmp_path).plan_input(RunConfig())
    _, vocabulary = playbook("banking")
    check_plan(Plan.model_validate(PLAN), source, vocabulary)
    broken = json.loads(json.dumps(PLAN))
    change(broken)
    with pytest.raises(ValueError, match=message):
        check_plan(Plan.model_validate(broken), source, vocabulary)


async def test_invalid_plan_is_repaired_once(tmp_path: Path, journal: Journal) -> None:
    attempts: list[str] = []

    def model(messages: list[ModelMessage], info: AgentInfo) -> ModelResponse:
        bad = json.loads(json.dumps(PLAN))
        bad["steps"][0]["action"] = "send_email"
        attempts.append("x")
        return reply(info, bad if len(attempts) == 1 else PLAN)

    runtime = CaseRuntime(FunctionModel(model), RunConfig(), journal)
    result = await plan_case(
        runtime, session(tmp_path).plan_input(RunConfig()), PlannerConfig(skill_selection="all")
    )
    assert result["status"] == "available" and len(attempts) == 2
    assert result["plan"]["steps"][0]["action"] == "read_document"


async def test_solver_receives_advisory_plan_and_snapshot_keeps_it(
    tmp_path: Path, journal: Journal
) -> None:
    seen: dict[str, str] = {}

    def planner(messages: list[ModelMessage], info: AgentInfo) -> ModelResponse:
        assert not info.function_tools
        payload = json.loads(str(getattr(messages[0].parts[-1], "content", "")))
        assert payload["case_id"] == "banking-005"
        return reply(info, PLAN)

    def solver(messages: list[ModelMessage], info: AgentInfo) -> ModelResponse:
        seen["instructions"] = info.instructions or ""
        return reply(info, ANSWER)

    config = RunConfig(planner=PlannerConfig(skill_selection="all"))
    runtime = CaseRuntime(
        FunctionModel(solver), config, journal, planner_model=FunctionModel(planner)
    )
    subject = session(tmp_path)
    output = await subject.run(runtime)
    assert output.agent_disposition == "escalated"
    assert "Planner decision of record" in seen["instructions"]
    assert "Registration does not confirm a return" in seen["instructions"]
    assert subject.snapshot()["plan"]["status"] == "available"
    assert [r["role"] for r in runtime.role_records] == ["planner", "subject"]


async def test_planner_failure_never_blocks_the_solver(tmp_path: Path, journal: Journal) -> None:
    seen: dict[str, str] = {}

    def model(messages: list[ModelMessage], info: AgentInfo) -> ModelResponse:
        if info.output_tools[0].name == "case_plan":
            return reply(info, {"intent": "incomplete"})
        seen["instructions"] = info.instructions or ""
        return reply(info, ANSWER)

    runtime = CaseRuntime(
        FunctionModel(model), RunConfig(planner=PlannerConfig(skill_selection="all")), journal
    )
    subject = session(tmp_path)
    await subject.run(runtime)
    assert subject.snapshot()["plan"]["status"] == "error"
    assert "Planner decision of record" not in seen["instructions"]


async def test_planner_off_by_default_and_when_disabled(tmp_path: Path, journal: Journal) -> None:
    def model(messages: list[ModelMessage], info: AgentInfo) -> ModelResponse:
        assert info.output_tools[0].name == "case_answer"
        return reply(info, ANSWER)

    for index, config in enumerate([RunConfig(), RunConfig(planner=PlannerConfig(mode="off"))]):
        subject = session(tmp_path / str(index))
        await subject.run(CaseRuntime(FunctionModel(model), config, journal))
        assert "plan" not in subject.snapshot()


def test_cli_writes_json_inputs_without_model_calls(tmp_path: Path) -> None:
    source = session(tmp_path).plan_input(RunConfig())
    path = tmp_path / "input.json"
    path.write_text(source.model_dump_json())
    config = tmp_path / "config.json"
    config.write_text(json.dumps({"planner": {"mode": "advisory"}}))
    output = tmp_path / "out"
    assert (
        plan_cli(
            [
                "--input",
                str(path),
                "--config",
                str(config),
                "--output",
                str(output),
                "--inputs-only",
            ]
        )
        == 0
    )
    assert json.loads((output / "banking-005.input.json").read_text())["case_id"] == "banking-005"
    assert json.loads((output / "plans.json").read_text())[0]["status"] == "not_run"


@pytest.mark.parametrize("ids", [[], ["a", "a"], ["../outside"]])
async def test_planner_cli_rejects_bad_selection_before_writing(
    tmp_path: Path, ids: list[str]
) -> None:
    from dwelly_bot.planner.cli import run
    from dwelly_bot.planner.contracts import PlanInput

    output = tmp_path / "out"
    sources = [PlanInput(case_id=id, decision_time="now", request="test") for id in ids]
    with pytest.raises(ValueError):
        await run(sources, RunConfig(), output, call=False)
    assert not output.exists()


def test_planner_cli_failure_exit_and_trace(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from contextlib import nullcontext

    import dwelly_bot.planner.cli as cli
    from dwelly_bot.contracts import ModelProfile
    from dwelly_bot.planner.contracts import PlanInput

    def fail(messages: list[ModelMessage], info: AgentInfo) -> ModelResponse:
        raise RuntimeError("test failure")

    def transport(profile: ModelProfile) -> Any:
        return nullcontext(FunctionModel(fail)), profile

    monkeypatch.setattr(cli, "transport", transport)
    source = tmp_path / "case.input.json"
    source.write_text(
        PlanInput(case_id="case", decision_time="now", request="test").model_dump_json()
    )
    config = tmp_path / "config.json"
    config.write_text(RunConfig(budget_file=str(tmp_path / "budget.json")).model_dump_json())
    output = tmp_path / "out"
    assert cli.main(["--input", str(source), "--config", str(config), "--output", str(output)]) == 1
    trace = json.loads((output / "journals/case.jsonl").read_text().splitlines()[-1])
    assert trace["roles"][0]["role"] == "planner"
    assert trace["costs"] and trace["config"]
