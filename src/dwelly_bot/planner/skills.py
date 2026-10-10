"""Select packaged knowledge without granting the planner tools or filesystem access."""

import hashlib

from pydantic import BaseModel, ConfigDict, Field, TypeAdapter
from pydantic_ai.exceptions import ModelRetry

from dwelly_bot.contracts import PlannerConfig
from dwelly_bot.harness.runtime import CaseRuntime
from dwelly_bot.planner.contracts import PlanInput
from dwelly_bot.resources import text


class Skill(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: str = Field(pattern=r"^[a-z][a-z0-9-]*$")
    description: str = Field(min_length=1)
    sources: list[str]

    @property
    def resource(self) -> str:
        return f"planner/skills/{self.id}/SKILL.md"


class SkillSelection(BaseModel):
    model_config = ConfigDict(extra="forbid")
    skill_ids: list[str] = Field(max_length=6)


def catalog(playbook: str) -> list[Skill]:
    # A new domain must supply its own catalog rather than inherit banking guidance.
    if playbook != "banking":
        raise ValueError(f"No skill catalog registered for playbook: {playbook}")
    skills = TypeAdapter(list[Skill]).validate_json(text("planner/skills/catalog.json"))
    if len({s.id for s in skills}) != len(skills):
        raise ValueError("Duplicate Planner skill IDs")
    return skills


def receipt(resource: str, content: str) -> dict[str, str]:
    return {"resource": resource, "sha256": hashlib.sha256(content.encode()).hexdigest()}


async def select_skills(
    runtime: CaseRuntime, source: PlanInput, config: PlannerConfig
) -> list[tuple[str, str]]:
    """Selection and planning share the planner model, cumulative limits and captures.

    Invalid selection is repaired by the SDK. Exhausted retries or model/budget errors
    remain visible planner failures; never silently drop knowledge or bypass limits.
    """
    skills = catalog(config.playbook)
    catalog_text = text("planner/skills/catalog.json")
    selector_text = text("planner/select-skills.md")
    with runtime.journal.record(
        "select_planner_skills",
        {"mode": config.skill_selection, "case_id": source.case_id},
        kind="skill_selection",
        role="planner",
        read_only=True,
    ) as event:
        if config.skill_selection == "all":
            selected = {s.id for s in skills}
        else:
            agent = runtime.agent(
                output_type=SkillSelection,
                output_name="planner_skill_selection",
                instructions=selector_text + "\nTrusted catalog:\n" + catalog_text,
                role="planner",
            )

            @agent.output_validator
            def known(selection: SkillSelection) -> SkillSelection:
                ids = selection.skill_ids
                if len(ids) != len(set(ids)) or set(ids) - {s.id for s in skills}:
                    raise ModelRetry("Select unique skill IDs from the catalog only.")
                return selection

            result = await runtime.ask(agent, source.model_dump(mode="json"), role="planner")
            selected = set(SkillSelection.model_validate(result.output).skill_ids)
        loaded = [(s.resource, text(s.resource)) for s in skills if s.id in selected]
        runtime.journal.returned(
            event,
            {
                "selected": [s.id for s in skills if s.id in selected],
                "resources": [receipt(path, content) for path, content in loaded],
                "catalog": receipt("planner/skills/catalog.json", catalog_text),
                "selector": receipt("planner/select-skills.md", selector_text),
                "sources": sorted({r for s in skills if s.id in selected for r in s.sources}),
            },
        )
    return loaded
