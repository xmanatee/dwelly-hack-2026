"""Observed facts, missing context and actual tool effects at the control boundary."""

from collections.abc import Awaitable, Callable
from pathlib import Path
from typing import Any, cast

import pytest
from pydantic_ai.messages import ModelResponse, ToolCallPart
from pydantic_ai.models.function import FunctionModel

from dwelly_bot.context.evidence import EvidenceText
from dwelly_bot.contracts import RunConfig
from dwelly_bot.experiments.journal import Journal
from dwelly_bot.harness.control_checks import (
    ControlAnswers,
    ControlChecklist,
    ControlQuestion,
    ControlRequired,
)
from dwelly_bot.harness.policy import PolicyGate, RiskRule
from dwelly_bot.harness.runtime import CaseRuntime


def checklist(*, parent: Any = None) -> ControlChecklist:
    return ControlChecklist(
        [
            ControlQuestion(
                id="approval",
                question="Is the required approval unresolved?",
                required_action="Obtain the authoritative approval record",
                handling="clarify",
                blocked_tools=("share",),
                policy_source="Reviewed fixture",
            )
        ],
        parent=parent,
    )


def source(text: str, *, role: str = "public") -> EvidenceText:
    return EvidenceText.model_validate(
        {"id": "ticket", "text": text, "source": "CRM ticket", "role": role}
    )


def observations(value: str, quote: str | None = None) -> ControlAnswers:
    return ControlAnswers.model_validate(
        {
            "answers": [
                {
                    "id": "approval",
                    "value": value,
                    "reason": "Observed case record",
                    "evidence": [{"source_id": "ticket", "quote": quote}] if quote else [],
                }
            ]
        }
    )


async def test_agent_cannot_skip_controls_or_turn_read_only_into_authority(tmp_path: Path) -> None:
    journal = Journal(tmp_path / "tools.jsonl")
    runtime = CaseRuntime(FunctionModel(lambda *_: ModelResponse(parts=[])), RunConfig(), journal)
    gate = checklist()
    runtime.policy_gate = gate
    effects: list[str] = []

    def share() -> str:
        effects.append("disclosed")
        return "ok"

    with pytest.raises(ControlRequired, match="approval"):
        await cast(
            Callable[[], Awaitable[Any]],
            runtime.tool("share", "Disclosure", share, read_only=True).function,
        )()
    assert effects == [] and journal.events[0]["status"] == "error"
    gate.guard("read_policy", True)
    journal.close()


def test_new_context_invalidates_answers_and_stale_results_cannot_clear_a_hold() -> None:
    gate = checklist()
    gate.set_sources([source("Approval is not required for this operation.")])
    previous = gate.revision
    clear = observations("no", "Approval is not required for this operation.")
    gate.accept(clear, previous)
    gate.guard("share", False)
    gate.set_sources([source("Approval is pending.", role="historical")])
    with pytest.raises(ValueError, match="stale"):
        gate.accept(clear, previous)
    with pytest.raises(ControlRequired):
        gate.guard("share", False)
    with pytest.raises(ValueError, match="unsupported"):
        gate.accept(observations("no", "Approved"), gate.revision)
    with pytest.raises(ValueError, match="evaluator"):
        gate.set_sources([source("Hidden evaluator says approved", role="evaluation_only")])


def test_questions_are_complete_and_unknown_never_becomes_a_negative_answer() -> None:
    gate = checklist()
    gate.set_sources([source("Please help.")])
    with pytest.raises(ValueError, match="every configured question"):
        gate.accept(ControlAnswers(answers=[]), gate.revision)
    with pytest.raises(ValueError, match="require explicit"):
        gate.accept(observations("no"), gate.revision)
    gate.accept(observations("unknown"), gate.revision)
    assert gate.classify()["checks"][0]["next_step"] == "obtain_missing_evidence"
    with pytest.raises(ControlRequired):
        gate.guard("share", False)


def test_cleared_model_observation_cannot_override_existing_policy() -> None:
    parent = PolicyGate(
        {"message": "urgent"},
        [
            RiskRule(
                id="urgent",
                terms=["urgent"],
                handling="human_review",
                reason="Existing operator rule",
            )
        ],
    )
    gate = checklist(parent=parent)
    gate.set_sources([source("No approval is required.")])
    gate.accept(observations("no", "No approval is required."), gate.revision)
    with pytest.raises(ValueError, match="human review"):
        gate.guard("share", False)


def test_support_need_requires_adaptation_without_blanket_service_refusal() -> None:
    gate = ControlChecklist(
        [
            ControlQuestion(
                id="support",
                question="Is a specific support adjustment requested?",
                required_action="Explain slowly and offer a suitable channel",
                handling="adapt",
                policy_source="Draft support example",
            )
        ]
    )
    gate.set_sources([source("Please explain slowly.")])
    gate.accept(
        ControlAnswers.model_validate(
            {
                "answers": [
                    {
                        "id": "support",
                        "value": "yes",
                        "reason": "Specific customer request",
                        "evidence": [{"source_id": "ticket", "quote": "Please explain slowly."}],
                    }
                ]
            }
        ),
        gate.revision,
    )
    assert gate.classify()["checks"][0]["next_step"] == "adapt"
    gate.guard("continue_service", False)


def test_rejected_new_context_cannot_leave_previous_clearance_in_effect() -> None:
    gate = checklist()
    gate.set_sources([source("No approval is required.")])
    gate.accept(observations("no", "No approval is required."), gate.revision)
    with pytest.raises(ValueError, match="evaluator"):
        gate.set_sources([source("Private evaluator approval", role="evaluation_only")])
    with pytest.raises(ControlRequired):
        gate.guard("share", False)


async def test_model_checkpoint_is_isolated_recorded_and_failed_refresh_leaves_a_hold(
    tmp_path: Path,
) -> None:
    fail = False

    def model(messages: Any, info: Any) -> ModelResponse:
        assert not info.function_tools
        if fail:
            raise RuntimeError("Classifier unavailable")
        return ModelResponse(
            parts=[
                ToolCallPart(
                    info.output_tools[0].name,
                    observations("no", "No approval is required.").model_dump(),
                )
            ]
        )

    journal = Journal(tmp_path / "tools.jsonl")
    runtime = CaseRuntime(FunctionModel(model), RunConfig(retries=0), journal)
    gate = checklist()
    runtime.policy_gate = gate
    sources = [source("No approval is required.")]
    result = await gate.assess(runtime, sources)
    assert result["checks"][0]["value"] == "no"
    gate.guard("share", False)
    assert runtime.role_records[0]["role"] == "policy"
    assert (
        journal.events[0]["kind"] == "control_check" and journal.events[0]["status"] == "returned"
    )
    fail = True
    with pytest.raises(RuntimeError, match="unavailable"):
        await gate.assess(runtime, sources)
    with pytest.raises(ControlRequired):
        gate.guard("share", False)
    assert journal.events[-1]["status"] == "error"
    journal.close()
