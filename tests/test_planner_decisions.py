"""Final next-action contract, grounded public explanations and legacy capture loading."""

from copy import deepcopy
from typing import Any

import pytest

from dwelly_bot.planner import Plan, PlanInput
from dwelly_bot.planner.contracts import PlanDocument
from dwelly_bot.planner.planner import advisory, playbook
from dwelly_bot.planner.validate import check_plan
from hackathon_winner.generation import TemplateGenerator

SOURCE = PlanInput(
    case_id="hardship",
    decision_time="now",
    request="I lost my job, cannot meet repayments and want a person to help.",
)
DECISION: dict[str, Any] = {
    "intent": "hardship-support",
    "summary": "Transfer this case to financial difficulty support now.",
    "identity_authority": "not_needed",
    "safety_flags": ["financial_difficulty"],
    "expected_disposition": "escalated",
    "steps": [
        {
            "id": "s1",
            "kind": "proposed_action",
            "action": "refer_specialist",
            "instruction": "Send this repayment-support case to the financial difficulty support role with the reported job loss and request to speak to a person; do not agree new loan terms.",
            "target": "financial difficulty support role",
            "rationale": {
                "explanation": "The customer reports inability to meet repayments and explicitly requests human support.",
                "evidence": ["request"],
                "criterion": "Disclosed repayment difficulty and requested human support warrant a specialist handoff.",
                "source": "skill:vulnerability-support",
            },
        }
    ],
}


def validate(payload: dict[str, Any], skills: set[str] | None = None) -> None:
    check_plan(
        Plan.model_validate(payload),
        SOURCE,
        playbook("banking")[1],
        require_decision=True,
        selected_skills=skills if skills is not None else {"vulnerability-support"},
    )


def test_decided_step_has_separate_instruction_and_grounds() -> None:
    validate(DECISION)
    encoded = Plan.model_validate(DECISION).model_dump()
    assert "purpose" not in encoded["steps"][0]
    assert encoded["steps"][0]["rationale"] == DECISION["steps"][0]["rationale"]
    context = advisory(encoded)
    assert "decision of record" in context and "stop the affected action" in context
    assert "where you deviate" not in context


def test_input_rejects_colliding_evidence_ids() -> None:
    import pytest

    for documents in [
        [PlanDocument(name="request", text="ambiguous")],
        [
            PlanDocument(name="context.md", text="first"),
            PlanDocument(name="context.md", text="second"),
        ],
    ]:
        with pytest.raises(ValueError, match="unique"):
            PlanInput(case_id="case", decision_time="now", request="help", documents=documents)


@pytest.mark.parametrize(
    ("field", "value", "error"),
    [
        ("rationale", None, "separate rationale"),
        ("condition", "If we later determine this is hardship", "no hypothetical condition"),
        ("instruction", "   ", "concrete instruction"),
    ],
)
def test_non_decisions_cannot_pass_live_checks(field: str, value: Any, error: str) -> None:
    payload = deepcopy(DECISION)
    payload["steps"][0][field] = value
    with pytest.raises(ValueError, match=error):
        validate(payload)


@pytest.mark.parametrize(
    ("field", "value", "error"),
    [
        ("evidence", ["future-event"], "unknown evidence"),
        ("source", "law:made-up-clause", "unknown or unloaded rule source"),
        ("source", "skill:financial-abuse", "unknown or unloaded rule source"),
        ("source", "evidence:missing-policy.md", "unknown or unloaded rule source"),
    ],
)
def test_grounds_cannot_cite_absent_evidence_or_unloaded_rules(
    field: str, value: Any, error: str
) -> None:
    payload = deepcopy(DECISION)
    payload["steps"][0]["rationale"][field] = value
    with pytest.raises(ValueError, match=error):
        validate(payload)


def test_hypothetical_escalation_cannot_replace_current_decision() -> None:
    payload = deepcopy(DECISION)
    payload["escalate_if"] = ["If a later investigation discovers vulnerability"]
    with pytest.raises(ValueError, match="Decide any needed escalation now"):
        validate(payload)


def test_unknown_identity_cannot_be_assumed_successful_in_a_later_step() -> None:
    payload = deepcopy(DECISION)
    payload["identity_authority"] = "unclear"
    first = payload["steps"][0]
    first["action"] = "confirm_identity_authority"
    payload["steps"].append(
        {**first, "id": "s2", "action": "request_confirmation", "requires": ["s1"]}
    )
    payload["safety_flags"] = []
    with pytest.raises(ValueError, match="do not schedule a change"):
        validate(payload)


async def test_legacy_capture_stays_readable_without_fabricating_grounds() -> None:
    payload = deepcopy(DECISION)
    step = payload["steps"][0]
    step["purpose"] = step.pop("instruction")
    step.pop("rationale")
    plan = Plan.model_validate(payload)
    assert plan.steps[0].instruction and plan.steps[0].rationale is None
    check_plan(plan, SOURCE, playbook("banking")[1])
    generated = await TemplateGenerator().generate(plan, SOURCE.request)
    assert "no separate rationale recorded" in generated.reasoning
    with pytest.raises(ValueError, match="separate rationale"):
        validate(payload)


async def test_winner_preserves_decision_grounds_without_another_model() -> None:
    generated = await TemplateGenerator().generate(Plan.model_validate(DECISION), SOURCE.request)
    step = DECISION["steps"][0]
    assert step["instruction"] in generated.answer
    for key in ("explanation", "criterion", "source"):
        assert step["rationale"][key] in generated.reasoning
    assert "request" in generated.reasoning


def test_escalated_disposition_requires_a_handoff_action() -> None:
    payload = deepcopy(DECISION)
    payload["safety_flags"] = []
    payload["steps"][0]["action"] = "reply_to_customer"
    with pytest.raises(ValueError, match="explicit handoff"):
        validate(payload)


def test_reading_alone_is_not_a_decision() -> None:
    from dwelly_bot.planner.contracts import ToolSpec

    payload = deepcopy(DECISION)
    payload["safety_flags"] = []
    payload["expected_disposition"] = "needs_info"
    payload["steps"][0].update(kind="solver_tool", action="read_document")
    source = SOURCE.model_copy(
        update={"solver_tools": [ToolSpec(name="read_document", description="Read supplied text")]}
    )
    with pytest.raises(ValueError, match="not stop at reading"):
        check_plan(
            Plan.model_validate(payload),
            source,
            playbook("banking")[1],
            require_decision=True,
            selected_skills={"vulnerability-support"},
        )
