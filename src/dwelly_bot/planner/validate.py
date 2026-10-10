"""Deterministic plan checks; a failed check is sent back to the planner once for repair."""

from dwelly_bot.planner.contracts import Plan, PlanInput, Playbook


def check_plan(
    plan: Plan,
    source: PlanInput,
    playbook: Playbook,
    *,
    require_decision: bool = False,
    selected_skills: set[str] | None = None,
) -> None:
    errors: list[str] = []
    tools = {tool.name: tool for tool in source.solver_tools}
    evidence = source.evidence_ids()
    seen: set[str] = set()
    rule_sources = {
        "general:planner",
        "general:evidence",
        "general:safety",
        *(f"evidence:{id}" for id in evidence),
        *(f"skill:{id}" for id in selected_skills or set()),
    }
    for step in plan.steps:
        if require_decision:
            if not step.instruction.strip():
                errors.append(f"{step.id}: concrete instruction is required")
            if step.condition is not None:
                errors.append(
                    f"{step.id}: decide the current action; no hypothetical condition. Request missing input or hand off now instead"
                )
            if step.rationale is None:
                errors.append(
                    f"{step.id}: separate rationale with evidence, criterion and source is required"
                )
            else:
                if unknown := set(step.rationale.evidence) - evidence:
                    errors.append(f"{step.id}: rationale cites unknown evidence {sorted(unknown)}")
                if step.rationale.source not in rule_sources:
                    errors.append(
                        f"{step.id}: unknown or unloaded rule source {step.rationale.source!r}"
                    )
        if step.id in seen:
            errors.append(f"Duplicate step ID {step.id}")
        if set(step.requires) - seen:
            errors.append(f"{step.id} requires steps that do not come earlier")
        seen.add(step.id)
        if step.kind == "solver_tool":
            tool = tools.get(step.action)
            if tool is None:
                errors.append(f"{step.id}: {step.action!r} is not a solver tool")
            elif set(step.arguments) - set(tool.parameters.get("properties", {})):
                errors.append(f"{step.id}: unknown arguments for {step.action}")
        elif step.action not in playbook.actions:
            errors.append(f"{step.id}: {step.action!r} is not a playbook action")
        elif step.arguments:
            errors.append(f"{step.id}: only solver_tool steps take arguments")
    for fact in plan.facts:
        if unknown := set(fact.evidence) - evidence:
            errors.append(f"Fact cites unknown evidence {sorted(unknown)}")
    proposed = [step.action for step in plan.steps if step.kind == "proposed_action"]
    if require_decision:
        if not proposed:
            errors.append("The plan must decide a next action, not stop at reading evidence")
        if plan.expected_disposition == "escalated" and not set(proposed) & {
            "refer_specialist",
            "escalate_urgent",
            "request_team_action",
        }:
            errors.append("An escalated decision requires an explicit handoff or team action")
        if plan.escalate_if:
            errors.append("Decide any needed escalation now; leave legacy escalate_if empty")
    for flag in plan.safety_flags:
        if flag not in playbook.safety_flags:
            errors.append(f"Unknown safety flag {flag!r}")
        elif missing := set(playbook.safety_flags[flag]) - set(proposed):
            errors.append(f"Safety flag {flag} requires actions {sorted(missing)}")
    if plan.identity_authority not in {"established", "not_needed"}:
        identity_seen = False
        for step in plan.steps:
            if require_decision and step.action in playbook.state_changing:
                errors.append(
                    f"{step.id}: decide verification/handoff now; do not schedule a change before authority is established. "
                    f"{step.action} is classified as state-changing regardless of its wording; "
                    "use an appropriate non-state-changing verification, secure-route or specialist-handoff action from the vocabulary"
                )
            identity_seen |= step.action in playbook.identity_actions
            if step.action in playbook.state_changing and not identity_seen:
                errors.append(
                    f"{step.id}: {step.action} changes state before identity/authority is established"
                )
    if errors:
        raise ValueError("; ".join(errors))
