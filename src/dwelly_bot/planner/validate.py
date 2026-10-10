"""Deterministic plan checks; a failed check is sent back to the planner once for repair."""

from dwelly_bot.planner.contracts import Plan, PlanInput, Playbook


def check_plan(plan: Plan, source: PlanInput, playbook: Playbook) -> None:
    errors: list[str] = []
    tools = {tool.name: tool for tool in source.solver_tools}
    evidence = source.evidence_ids()
    seen: set[str] = set()
    for step in plan.steps:
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
    for flag in plan.safety_flags:
        if flag not in playbook.safety_flags:
            errors.append(f"Unknown safety flag {flag!r}")
        elif missing := set(playbook.safety_flags[flag]) - set(proposed):
            errors.append(f"Safety flag {flag} requires actions {sorted(missing)}")
    if plan.identity_authority not in {"established", "not_needed"}:
        identity_seen = False
        for step in plan.steps:
            identity_seen |= step.action in playbook.identity_actions
            if step.action in playbook.state_changing and not identity_seen:
                errors.append(
                    f"{step.id}: {step.action} changes state before identity/authority is established"
                )
    if errors:
        raise ValueError("; ".join(errors))
