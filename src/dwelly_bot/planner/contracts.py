"""Planner input and plan schemas; the planner's whole interface to the rest of the app."""

from __future__ import annotations

from typing import Any, Literal, Self

from pydantic import AliasChoices, BaseModel, ConfigDict, Field, model_validator


class ToolSpec(BaseModel):
    """A solver tool as the solver will see it; built from the solver's own bindings."""

    model_config = ConfigDict(extra="forbid")
    name: str
    description: str
    parameters: dict[str, Any] = Field(default_factory=dict)
    read_only: bool = True


class PlanEvent(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: str
    at: str
    channel: str
    sender: str
    recipient: str
    text: str


class PlanDocument(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str
    text: str


class PlanInput(BaseModel):
    """All context available at the decision point; nothing later is ever included."""

    model_config = ConfigDict(extra="forbid")
    case_id: str
    decision_time: str
    request: str
    task: str = ""
    events: list[PlanEvent] = Field(default_factory=list)
    documents: list[PlanDocument] = Field(default_factory=list)
    datapoints: dict[str, Any] = Field(default_factory=dict)
    solver_tools: list[ToolSpec] = Field(default_factory=list)

    @model_validator(mode="after")
    def unique_evidence(self) -> Self:
        ids = ["request", *(e.id for e in self.events), *(d.name for d in self.documents)]
        if any(not key.strip() for key in ids) or len(ids) != len(set(ids)):
            raise ValueError(
                "Case evidence IDs must be nonempty and unique, including reserved request"
            )
        return self

    def evidence_ids(self) -> set[str]:
        return {"request", *(e.id for e in self.events), *(d.name for d in self.documents)}


class Fact(BaseModel):
    model_config = ConfigDict(extra="forbid")
    claim: str = Field(min_length=1)
    evidence: list[str] = Field(min_length=1, description="Evidence IDs from the input")


class StepRationale(BaseModel):
    """Public decision grounds, not a private reasoning transcript."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    explanation: str = Field(min_length=1, description="Why this action is the chosen next move")
    evidence: list[str] = Field(min_length=1, description="Input event/document IDs or request")
    criterion: str = Field(min_length=1, description="The applicable rule or decision criterion")
    source: str = Field(
        min_length=1,
        description="general:planner/evidence/safety, skill:<selected-id>, or evidence:<input-id>; never an invented law or policy reference",
    )


class PlanStep(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: str = Field(pattern=r"^s\d+$")
    kind: Literal["solver_tool", "proposed_action"] = Field(
        description="solver_tool: a listed tool operation; proposed_action: a decided bank operation pending execution, not an optional suggestion"
    )
    action: str = Field(
        description="Tool name for solver_tool; playbook action for proposed_action"
    )
    instruction: str = Field(
        min_length=1,
        validation_alias=AliasChoices("instruction", "purpose"),
        description="Concrete instruction: what to do now, to which case/party, with the known parameters or message. No further business decision is delegated.",
    )
    # Historical captures lacked separate grounds. Live make_plan rejects their absence.
    rationale: StepRationale | None = Field(
        default=None,
        description="Required for every newly generated step; null only in legacy saved plans",
    )
    target: str | None = Field(
        default=None, description="System, team, party or channel the step addresses"
    )
    arguments: dict[str, Any] = Field(
        default_factory=dict, description="Suggested tool arguments; solver_tool only"
    )
    requires: list[str] = Field(default_factory=list, description="Earlier step IDs")
    condition: str | None = Field(
        default=None,
        description="Legacy field; new decisions leave this null and decide only the current next actions",
    )


class Plan(BaseModel):
    model_config = ConfigDict(extra="forbid")
    intent: str = Field(min_length=1)
    summary: str = Field(
        min_length=1,
        max_length=600,
        description="Final selected decision at this snapshot, not a menu of possible strategies",
    )
    facts: list[Fact] = Field(default_factory=list)
    missing: list[str] = Field(default_factory=list)
    identity_authority: Literal["established", "not_established", "not_needed", "unclear"]
    safety_flags: list[str] = Field(default_factory=list)
    steps: list[PlanStep] = Field(min_length=1, max_length=12)
    escalate_if: list[str] = Field(
        default_factory=list,
        description="Legacy field; new decisions use explicit handoff actions now, not hypothetical future branches",
    )
    must_state: list[str] = Field(default_factory=list)
    must_not: list[str] = Field(default_factory=list)
    expected_disposition: Literal["completed", "needs_info", "escalated", "refused"]


class Playbook(BaseModel):
    """Machine-readable half of a playbook: the vocabulary plans are checked against."""

    model_config = ConfigDict(extra="forbid")
    actions: dict[str, str] = Field(min_length=1, description="action -> meaning")
    state_changing: list[str] = Field(default_factory=list)
    identity_actions: list[str] = Field(default_factory=list)
    safety_flags: dict[str, list[str]] = Field(
        default_factory=dict, description="flag -> proposed actions the plan must include"
    )
