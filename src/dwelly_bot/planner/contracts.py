"""Planner input and plan schemas; the planner's whole interface to the rest of the app."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


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

    def evidence_ids(self) -> set[str]:
        return {"request", *(e.id for e in self.events), *(d.name for d in self.documents)}


class Fact(BaseModel):
    model_config = ConfigDict(extra="forbid")
    claim: str = Field(min_length=1)
    evidence: list[str] = Field(min_length=1, description="Evidence IDs from the input")


class PlanStep(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: str = Field(pattern=r"^s\d+$")
    kind: Literal["solver_tool", "proposed_action"] = Field(
        description="solver_tool: a listed solver tool call; proposed_action: an action the solver proposes to a bank operator"
    )
    action: str = Field(
        description="Tool name for solver_tool; playbook action for proposed_action"
    )
    purpose: str = Field(min_length=1)
    target: str | None = Field(
        default=None, description="System, team, party or channel the step addresses"
    )
    arguments: dict[str, Any] = Field(
        default_factory=dict, description="Suggested tool arguments; solver_tool only"
    )
    requires: list[str] = Field(default_factory=list, description="Earlier step IDs")
    condition: str | None = Field(default=None, description="When to take this step")


class Plan(BaseModel):
    model_config = ConfigDict(extra="forbid")
    intent: str = Field(min_length=1)
    summary: str = Field(min_length=1, max_length=600)
    facts: list[Fact] = Field(default_factory=list)
    missing: list[str] = Field(default_factory=list)
    identity_authority: Literal["established", "not_established", "not_needed", "unclear"]
    safety_flags: list[str] = Field(default_factory=list)
    steps: list[PlanStep] = Field(min_length=1, max_length=12)
    escalate_if: list[str] = Field(default_factory=list)
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
