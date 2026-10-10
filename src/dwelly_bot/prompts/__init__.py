"""Named SDK instructions; case values remain data."""

from collections.abc import Iterable

from pydantic_ai import InstructionPart

from dwelly_bot.contracts import RunConfig
from dwelly_bot.paths import ROOT
from dwelly_bot.resources import text


def instructions(domain: str, config: RunConfig, *policies: str) -> list[InstructionPart]:
    parts = [
        InstructionPart(text("prompts/case-agent.md"), name="common"),
    ]
    if config.domain_skill_enabled:
        parts.append(InstructionPart(text(f"skills/{domain}.md"), name="domain"))
    parts.extend(
        InstructionPart(policy, name=f"policy-{i}", dynamic=True)
        for i, policy in enumerate(policies)
    )
    parts.extend(extras(config))
    return parts


def extras(config: RunConfig) -> Iterable[InstructionPart]:
    if config.instructions.strip():
        yield InstructionPart(config.instructions, name="variant")
    if config.skills and config.skill_mode == "on_demand":
        yield InstructionPart(
            "Optional trusted workflow instructions are available through list_skills/read_skill. "
            "Read relevant skills before applying them; preserve operating policy, authority checks and observed facts.",
            name="skill-library",
        )
        return
    for index, path in enumerate(config.skills):
        yield InstructionPart((ROOT / path).read_text(encoding="utf-8"), name=f"skill-{index}")
