"""Hackathon Solver generation: plan stays the decision; nothing reported as done; safe export."""

import json
from pathlib import Path
from typing import Any

import pytest
from pydantic_ai.messages import ModelMessage, ModelResponse, ToolCallPart
from pydantic_ai.models.function import AgentInfo, FunctionModel

from dwelly_bot.contracts import RunConfig
from dwelly_bot.experiments.journal import Journal
from dwelly_bot.harness.runtime import CaseRuntime
from dwelly_bot.planning.contracts import Handoff, Plan, ReplyToTrigger
from hackathon_winner.cli import main as solver_cli
from hackathon_winner.export import check_output, write_case
from hackathon_winner.generation import EXECUTED_CLAIM, ModelGenerator, TemplateGenerator

PLAN = Plan(
    decision="Register a return request for the misdirected £286.40 transfer.",
    disposition="human_review",
    actions=(
        Handoff(id="review", queue="payment-team", reason="Register the return request."),
        ReplyToTrigger(id="reply", message="We will ask the payment team to seek the return."),
    ),
    rationale="Verified call; transfer shown as sent; a return is not guaranteed.",
)


async def test_template_keeps_decision_and_marks_actions_proposed() -> None:
    generated = await TemplateGenerator().generate(PLAN, "context")
    assert PLAN.decision in generated.answer
    assert "Hand off to the payment-team queue" in generated.answer
    assert "none has been carried out" in generated.answer
    assert "We will ask the payment team" in generated.answer
    assert PLAN.rationale in generated.reasoning
    assert "`review` (handoff): proposed, not executed" in generated.reasoning
    assert not EXECUTED_CLAIM.search(generated.answer + generated.reasoning)


async def test_model_claims_of_done_actions_are_repaired(tmp_path: Path) -> None:
    replies: list[dict[str, Any]] = [
        {"answer": "I have registered the return.", "reasoning": "Done."},
        {"answer": "A return request is proposed.", "reasoning": "Pending operator action."},
    ]
    prompts: list[str] = []

    def model(messages: list[ModelMessage], info: AgentInfo) -> ModelResponse:
        prompts.append(str(getattr(messages[0].parts[-1], "content", "")))
        return ModelResponse(parts=[ToolCallPart(info.output_tools[0].name, replies.pop(0))])

    journal = Journal(tmp_path / "events.jsonl")
    runtime = CaseRuntime(FunctionModel(model), RunConfig(), journal)
    try:
        generated = await ModelGenerator(runtime).generate(PLAN, "VISIBLE_CONTEXT")
    finally:
        journal.close()
    assert generated.answer == "A return request is proposed."
    assert "decision of record" in prompts[0] and "VISIBLE_CONTEXT" in prompts[0]
    assert not replies
    assert runtime.role_records[0]["role"] == "generator"


def test_export_refuses_practice_answers_and_overwrites(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="practice"):
        check_output(tmp_path / "ANSWERS", development=True)
    (tmp_path / "out").mkdir()
    (tmp_path / "out" / "old.md").write_text("x")
    with pytest.raises(ValueError, match="empty"):
        check_output(tmp_path / "out", development=False)
    with pytest.raises(ValueError, match="Unsafe"):
        write_case(tmp_path, "../x", None, plan=PLAN, context="", generator={})  # type: ignore[arg-type]


def test_cli_writes_two_files_and_audit_record(tmp_path: Path) -> None:
    source = tmp_path / "in"
    source.mkdir()
    (source / "banking-005.plan.json").write_text(PLAN.model_dump_json())
    (source / "banking-005.context.md").write_text("# Initial request\n\nPlease seek a return.\n")
    output = tmp_path / "review"
    assert (
        solver_cli(["generate", "--input", str(source), "--output", str(output), "--development"])
        == 0
    )
    case = output / "banking-005"
    assert sorted(p.name for p in case.iterdir()) == [
        "ANSWER.md",
        "REASONING.md",
        "context.md",
        "generation.json",
        "plan.json",
    ]
    record = json.loads((case / "generation.json").read_text())
    assert record["generator"] == {"kind": "template"}
    assert record["plan"]["decision"] == PLAN.decision
    assert "Please seek a return." in record["context"]


async def test_template_renders_case_planner_plans_as_proposals() -> None:
    from dwelly_bot.planner.contracts import Plan as CasePlan

    plan = CasePlan.model_validate(
        {
            "intent": "payments.stop_return",
            "summary": "Register a return request for the verified transfer.",
            "facts": [{"claim": "Identity checks complete", "evidence": ["event-002"]}],
            "missing": ["Receiving bank response"],
            "identity_authority": "established",
            "safety_flags": [],
            "steps": [
                {
                    "id": "s1",
                    "kind": "solver_tool",
                    "action": "read_document",
                    "purpose": "Read history",
                },
                {
                    "id": "s2",
                    "kind": "proposed_action",
                    "action": "request_team_action",
                    "purpose": "Register the return request",
                    "target": "payment team",
                },
            ],
            "must_state": ["Registration does not confirm a return"],
            "expected_disposition": "escalated",
        }
    )
    generated = await TemplateGenerator().generate(plan, "context")
    assert "1. [s2] Register the return request (payment team)" in generated.answer
    assert "Read history" not in generated.answer
    assert "Registration does not confirm a return" in generated.answer
    assert "Identity checks complete (event-002)" in generated.reasoning
    assert not EXECUTED_CLAIM.search(generated.answer + generated.reasoning)


def test_html_report_escapes_case_text(tmp_path: Path) -> None:
    from hackathon_winner.export.html import render

    case = tmp_path / "banking-001"
    case.mkdir()
    (case / "ANSWER.md").write_text("## Decision\n\n- Check **record** <script>alert(1)</script>\n")
    (case / "REASONING.md").write_text("Grounds `event-002`.\n")
    (case / "generation.json").write_text(
        json.dumps(
            {
                "plan": {"summary": "S", "steps": [], "safety_flags": ["privacy"]},
                "context": "<b>x</b>",
            }
        )
    )
    (tmp_path / "predictions.json").write_text(
        json.dumps(
            {
                "dataset": "dwelly-banking",
                "cases": [
                    {
                        "case_id": "banking-001",
                        "planner": "available",
                        "generator": "model",
                        "requests": 2,
                        "cost_usd": 0.01,
                    }
                ],
            }
        )
    )
    page = render(tmp_path).read_text()
    assert "<script>alert(1)</script>" not in page and "&lt;script&gt;" in page
    assert "<strong>record</strong>" in page and "<code>event-002</code>" in page
    assert "&lt;b&gt;x&lt;/b&gt;" in page and "privacy" in page


def test_history_adapter_reads_only_history(tmp_path: Path) -> None:
    from dwelly_bot.contracts import RunConfig
    from hackathon_winner.adapters import load

    folder = tmp_path / "track" / "005"
    folder.mkdir(parents=True)
    (folder / "index.md").write_text("## Next action at escalation\n\nINDEX_SECRET\n")
    (folder / "history.md").write_text(
        "# Case 005 history — Wrong recipient\n\nTotal events: 2\n\n"
        '<a id="event-001"></a>\n## 2025-07-27 09:00:00 UTC — event 001\n\n'
        "- **Channel:** Secure portal\n- **From:** Harrow & Vale Bank plc\n- **To:** Leona\n\nSent.\n\n"
        '<a id="event-002"></a>\n## 2025-07-27 09:47:00 UTC — event 002\n\n'
        "- **Channel:** Verified call\n- **From:** Leona\n- **To:** H&V service agent\n\n"
        "Please seek a return.\n"
    )
    [case] = load(tmp_path / "track", RunConfig())
    assert case.case_id == "banking-005" and len(case.source.events) == 2
    assert case.source.request == "Please seek a return."
    assert "INDEX_SECRET" not in case.source.model_dump_json() + case.history


async def test_template_preserves_calculations_and_conditional_steps() -> None:
    from dwelly_bot.planner.contracts import Plan as CasePlan
    from dwelly_bot.planning.contracts import Calculate

    plan = PLAN.model_copy(
        update={
            "actions": (
                Calculate(
                    id="fee", expression="10 * 0.2", rounding="cents", basis="Supplied tariff"
                ),
            )
        }
    )
    answer = await TemplateGenerator().generate(plan, "")
    assert "10 * 0.2" in answer.answer and "Supplied tariff" in answer.answer
    advisory = CasePlan.model_validate(
        {
            "intent": "test",
            "summary": "Conditional escalation",
            "identity_authority": "unclear",
            "expected_disposition": "escalated",
            "must_not": ["Promise a refund"],
            "steps": [
                {
                    "id": "s1",
                    "kind": "proposed_action",
                    "action": "request_team_action",
                    "purpose": "Escalate",
                    "condition": "Customer agrees",
                }
            ],
        }
    )
    answer = await TemplateGenerator().generate(advisory, "")
    assert "Only if: Customer agrees" in answer.answer
    assert "Must not: Promise a refund" in answer.reasoning


async def test_generator_respects_runtime_request_limit(tmp_path: Path) -> None:
    from pydantic_ai.exceptions import UsageLimitExceeded

    def respond(messages: list[ModelMessage], info: AgentInfo) -> ModelResponse:
        assert info.model_settings and info.model_settings["max_tokens"] == 512
        return ModelResponse(
            parts=[
                ToolCallPart(
                    info.output_tools[0].name,
                    {"answer": "I have refunded the customer.", "reasoning": "Done."},
                )
            ]
        )

    journal = Journal(tmp_path / "events.jsonl")
    runtime = CaseRuntime(
        FunctionModel(respond), RunConfig(max_requests=1, max_tokens=512), journal
    )
    try:
        with pytest.raises(UsageLimitExceeded):
            await ModelGenerator(runtime).generate(PLAN, "context")
    finally:
        journal.close()
    assert len(runtime.role_records) == 1


@pytest.mark.parametrize("failure_stage", ["planner", "generator"])
def test_predict_retains_failures_and_continues_batch(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, failure_stage: str
) -> None:
    from contextlib import nullcontext

    import dwelly_bot.planner.cli as planner_cli
    from dwelly_bot.contracts import ModelProfile, PlannerConfig

    track = tmp_path / "cases"
    for case_id in ("001", "002"):
        folder = track / case_id
        folder.mkdir(parents=True)
        (folder / "history.md").write_text(
            "## 2026-01-01 09:00:00 UTC — event 001\n\n"
            "- **Channel:** Email\n- **From:** Customer\n- **To:** Bank\n\n"
            + ("FAIL_ME" if case_id == "001" else "Good request")
        )
    profiles: list[str] = []

    def respond(messages: list[ModelMessage], info: AgentInfo) -> ModelResponse:
        tool = info.output_tools[0].name
        stage = "planner" if tool in {"case_plan", "planner_skill_selection"} else "generator"
        if stage == failure_stage and "FAIL_ME" in str(messages):
            raise RuntimeError("simulated model failure")
        if tool == "planner_skill_selection":
            return ModelResponse(parts=[ToolCallPart(tool, {"skill_ids": ["payments"]})])
        if stage == "planner":
            return ModelResponse(
                parts=[
                    ToolCallPart(
                        tool,
                        {
                            "intent": "review",
                            "summary": "Ask a person to review",
                            "identity_authority": "unclear",
                            "expected_disposition": "escalated",
                            "steps": [
                                {
                                    "id": "s1",
                                    "kind": "proposed_action",
                                    "action": "reply_to_customer",
                                    "purpose": "Explain the next step",
                                }
                            ],
                        },
                    )
                ]
            )
        return ModelResponse(
            parts=[ToolCallPart(tool, {"answer": "Proposed review", "reasoning": "Needs review"})]
        )

    def transport(profile: ModelProfile) -> Any:
        profiles.append(profile.model)
        return nullcontext(FunctionModel(respond)), profile

    monkeypatch.setattr(planner_cli, "transport", transport)
    config = tmp_path / "config.json"
    config.write_text(
        RunConfig(
            budget_file=str(tmp_path / "ledger.json"),
            max_requests=4,
            planner=PlannerConfig(model=ModelProfile(model="planner-test")),
        ).model_dump_json()
    )
    output = tmp_path / "out"
    assert (
        solver_cli(
            ["predict", "--cases", str(track), "--config", str(config), "--output", str(output)]
        )
        == 1
    )
    assert "planner-test" in profiles
    rows = json.loads((output / "predictions.json").read_text())["cases"]
    assert rows[0]["generator"] == f"{failure_stage}_error"
    assert rows[1]["planner"] == "available" and rows[1]["generator"] == "model"
    for row in rows:
        assert (output / row["case_id"] / "ANSWER.md").exists()
        trace = json.loads(
            (output / "journals" / f"{row['case_id']}.jsonl").read_text().splitlines()[-1]
        )
        assert trace["roles"] and trace["costs"]
        assert trace["config"]["max_requests"] == 4
    page = (output / "report.html").read_text()
    assert f"{failure_stage}_error" in page and "not a blind" in page


def test_empty_history_corpus_and_nested_answers_are_rejected(tmp_path: Path) -> None:
    from hackathon_winner.adapters import load

    with pytest.raises(ValueError, match="No history"):
        load(tmp_path, RunConfig())
    with pytest.raises(ValueError, match="practice"):
        check_output(tmp_path / "ANSWERS" / "nested", development=True)


def test_winner_default_and_custom_output_preserve_case_folders(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from contextlib import nullcontext

    import dwelly_bot.planner.cli as planner_cli
    import hackathon_winner.cli as winner_cli
    import hackathon_winner.runner as winner_runner
    from dwelly_bot.contracts import ModelProfile
    from dwelly_bot.paths import ROOT
    from dwelly_bot.planner import Plan as ImportedPlan
    from dwelly_bot.planner import PlanInput, make_plan

    assert "steps" in ImportedPlan.model_fields and "events" in PlanInput.model_fields
    assert callable(make_plan)
    assert winner_runner.DEFAULT_OUTPUT == ROOT / "ANSWERS"

    def respond(messages: list[ModelMessage], info: AgentInfo) -> ModelResponse:
        tool = info.output_tools[0].name
        if tool == "planner_skill_selection":
            return ModelResponse(parts=[ToolCallPart(tool, {"skill_ids": ["payments"]})])
        if tool == "case_plan":
            result = {
                "intent": "review",
                "summary": "Explain the remaining uncertainty",
                "identity_authority": "not_needed",
                "expected_disposition": "needs_info",
                "steps": [
                    {
                        "id": "s1",
                        "kind": "proposed_action",
                        "action": "reply_to_customer",
                        "purpose": "Explain what is not confirmed",
                    }
                ],
            }
        else:
            result = {
                "answer": "Proposed response only.",
                "reasoning": "See context.md and event-001. Uncertainty remains.",
            }
        return ModelResponse(parts=[ToolCallPart(tool, result)])

    def transport(profile: ModelProfile) -> Any:
        return nullcontext(FunctionModel(respond)), profile

    monkeypatch.setattr(planner_cli, "transport", transport)
    config = tmp_path / "config.json"
    config.write_text(RunConfig(budget_file=str(tmp_path / "ledger.json")).model_dump_json())
    monkeypatch.setattr(winner_cli, "DEFAULT_CONFIG", config)
    default = tmp_path / "repo/ANSWERS"
    monkeypatch.setattr(winner_cli, "DEFAULT_OUTPUT", default)
    assert winner_cli.main([]) == 0
    custom = tmp_path / "evaluation"
    assert winner_cli.main([str(winner_runner.DEFAULT_CASES), "--output", str(custom)]) == 0
    for output in (default, custom):
        for case in ("001", "002"):
            for name in ("ANSWER.md", "REASONING.md", "plan.json", "context.md", "generation.json"):
                assert (output / case / name).is_file()
            assert not (output / f"banking-{case}").exists()
        rows = json.loads((output / "predictions.json").read_text())
        assert rows["development"] is True
        assert rows["cases"][1]["input_files"]["attachments/payment-screen.txt"]
        assert (output / "report.html").is_file()
    with pytest.raises(SystemExit) as failure:
        winner_cli.main([])
    assert failure.value.code == 2  # Existing generated answers are preserved.


def test_winner_plain_context_and_attachments_without_labels(tmp_path: Path) -> None:
    from hackathon_winner.adapters import load

    folder = tmp_path / "real-case-42"
    attachments = folder / "attachments"
    attachments.mkdir(parents=True)
    (folder / "context.md").write_text("Customer asks about a transfer; authentication unknown.")
    (folder / "index.md").write_text("PRIVATE_LABEL")
    (folder / "ANSWER.md").write_text("FUTURE_ANSWER")
    (attachments / "details.csv").write_text("reference,status\nTX-42,pending\n")
    (attachments / "scan.png").write_bytes(b"not-a-real-image")
    [case] = load(tmp_path, RunConfig(), prefix="")
    assert case.case_id == "real-case-42"
    assert case.source.events == [] and case.source.solver_tools == []
    assert "TX-42" in case.history and "Attachment unread" in case.history
    assert "PRIVATE_LABEL" not in case.history and "FUTURE_ANSWER" not in case.history
    assert {d.name for d in case.source.documents} == {
        "context.md",
        "attachments/details.csv",
        "attachments/scan.png",
    }
    assert set(case.input_files) == {
        "context.md",
        "attachments/details.csv",
        "attachments/scan.png",
    }


def test_winner_rejects_attachment_outside_case(tmp_path: Path) -> None:
    from hackathon_winner.adapters import load

    track = tmp_path / "cases"
    folder = track / "1"
    (folder / "attachments").mkdir(parents=True)
    (folder / "history.md").write_text("A supplied case")
    private = tmp_path / "private.txt"
    private.write_text("OUTSIDE_SECRET")
    (folder / "attachments/private.txt").symlink_to(private)
    with pytest.raises(ValueError, match="escapes"):
        load(track, RunConfig(), prefix="")
