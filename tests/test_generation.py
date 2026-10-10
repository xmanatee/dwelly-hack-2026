"""Hackathon Solver generation: plan stays the decision; nothing reported as done; safe export."""

import json
from pathlib import Path
from typing import Any

import pytest
from hackathon_solver.cli import main as solver_cli
from hackathon_solver.export import check_output, write_case
from hackathon_solver.generation import EXECUTED_CLAIM, ModelGenerator, TemplateGenerator
from pydantic_ai.messages import ModelMessage, ModelResponse, ToolCallPart
from pydantic_ai.models.function import AgentInfo, FunctionModel

from dwelly_bot.planning.contracts import Handoff, Plan, ReplyToTrigger

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


async def test_model_claims_of_done_actions_are_repaired() -> None:
    replies: list[dict[str, Any]] = [
        {"answer": "I have registered the return.", "reasoning": "Done."},
        {"answer": "A return request is proposed.", "reasoning": "Pending operator action."},
    ]
    prompts: list[str] = []

    def model(messages: list[ModelMessage], info: AgentInfo) -> ModelResponse:
        prompts.append(str(getattr(messages[0].parts[-1], "content", "")))
        return ModelResponse(parts=[ToolCallPart(info.output_tools[0].name, replies.pop(0))])

    generated = await ModelGenerator(FunctionModel(model)).generate(PLAN, "VISIBLE_CONTEXT")
    assert generated.answer == "A return request is proposed."
    assert "decision of record" in prompts[0] and "VISIBLE_CONTEXT" in prompts[0]
    assert not replies


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
        "generation.json",
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
    assert "1. Register the return request (payment team)" in generated.answer
    assert "Read history" not in generated.answer
    assert "Registration does not confirm a return" in generated.answer
    assert "Identity checks complete (event-002)" in generated.reasoning
    assert not EXECUTED_CLAIM.search(generated.answer + generated.reasoning)


def test_html_report_escapes_case_text(tmp_path: Path) -> None:
    from hackathon_solver.export.html import render

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
    from hackathon_solver.adapters import load

    from dwelly_bot.contracts import RunConfig

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
