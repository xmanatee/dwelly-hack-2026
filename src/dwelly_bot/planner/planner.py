"""Select a decision with public grounds; downstream roles implement or report it."""

import json
from typing import Any

from pydantic_ai import InstructionPart
from pydantic_ai.exceptions import ModelRetry

from dwelly_bot.contracts import PlannerConfig
from dwelly_bot.harness.runtime import CaseRuntime
from dwelly_bot.planner.contracts import Plan, PlanInput, Playbook
from dwelly_bot.planner.skills import receipt, select_skills
from dwelly_bot.planner.validate import check_plan
from dwelly_bot.resources import text


def playbook(name: str) -> tuple[str, Playbook]:
    prose = text(f"planner/playbooks/{name}.md")
    return prose, Playbook.model_validate_json(text(f"planner/playbooks/{name}.json"))


def instructions(
    config: PlannerConfig, skills: list[tuple[str, str]] | None = None
) -> list[InstructionPart]:
    prose, vocabulary = playbook(config.playbook)
    parts = [
        InstructionPart(text("planner/prompt.md"), name="planner"),
        InstructionPart(text("planner/evidence.md"), name="evidence"),
        InstructionPart(text("planner/safety.md"), name="safety"),
        InstructionPart(prose, name="playbook"),
        InstructionPart(
            "Allowed proposed actions and safety flags:\n" + vocabulary.model_dump_json(indent=2),
            name="vocabulary",
        ),
    ]
    parts.extend(InstructionPart(content, name=path) for path, content in skills or [])
    if config.instructions.strip():
        parts.append(InstructionPart(config.instructions, name="variant"))
    return parts


async def make_plan(runtime: CaseRuntime, source: PlanInput, config: PlannerConfig) -> Plan:
    _, vocabulary = playbook(config.playbook)
    skills = await select_skills(runtime, source, config)
    selected_ids = {path.split("/")[-2] for path, _ in skills}
    parts = instructions(config, skills)
    parts.append(
        InstructionPart(
            "Canonical case evidence IDs (use exactly these strings in facts and rationale; labels inside a document are not separate IDs):\n"
            + json.dumps(sorted(source.evidence_ids())),
            name="evidence-registry",
        )
    )
    with runtime.journal.record(
        "planner_instructions",
        {"case_id": source.case_id},
        kind="planner_instructions",
        role="planner",
        read_only=True,
    ) as event:
        runtime.journal.returned(
            event, {"parts": [receipt(str(part.name), part.content) for part in parts]}
        )
    agent = runtime.agent(
        output_type=Plan,
        output_name="case_plan",
        instructions=parts,
        role="planner",
    )

    @agent.output_validator
    def grounded(plan: Plan) -> Plan:
        try:
            check_plan(
                plan, source, vocabulary, require_decision=True, selected_skills=selected_ids
            )
        except ValueError as error:
            raise ModelRetry(
                f"Fix the plan: {error}. Allowed evidence IDs: {json.dumps(sorted(source.evidence_ids()))}"
            ) from error
        return plan

    result = await runtime.ask(agent, source.model_dump(mode="json"), role="planner")
    return Plan.model_validate(result.output)


async def plan_case(
    runtime: CaseRuntime, source: PlanInput, config: PlannerConfig
) -> dict[str, Any]:
    """A planner failure never blocks the solver; it is recorded and the solver runs unplanned."""
    try:
        plan = await make_plan(runtime, source, config)
    except Exception as error:
        return {"status": "error", "error": f"{type(error).__name__}: {error}"}
    return {"status": "available", "plan": plan.model_dump(mode="json")}


def advisory(plan: dict[str, Any]) -> str:
    return (
        "Planner decision of record for this snapshot. Carry out or describe these selected "
        "actions in order, preserving their instructions and public rationale. Do not choose "
        "a different strategy or repeat the planning pass. The plan is not evidence, an "
        "execution receipt or permission to bypass policy/tool limits. If new evidence "
        "contradicts the snapshot or a mandatory gate fails, stop the affected action and "
        "report the blocker for a fresh decision; never silently invent an alternative.\n"
        + json.dumps(plan, ensure_ascii=False, indent=1)
    )
