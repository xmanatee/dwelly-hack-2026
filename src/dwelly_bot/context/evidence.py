"""Small source-backed contracts reusable by analysis and the operational harness."""

from collections.abc import Iterable
from itertools import chain
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class EvidenceText(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: str
    text: str
    source: str
    role: Literal["public", "historical", "evaluation_only"] = "public"
    speaker: str | None = None
    timestamp: str | None = None
    origin: Literal["message", "document", "system_snapshot", "tool_event"] | None = None


class Citation(BaseModel):
    source_id: str
    quote: str = Field(min_length=1, description="Exact supporting substring from this source")


def check_citations(
    citations: Iterable[Citation], sources: Iterable[EvidenceText], *, unique: bool = True
) -> None:
    lookup: dict[str, str] = {}
    for source in sources:
        if source.role == "evaluation_only" or (
            source.id in lookup and (unique or lookup[source.id] != source.text)
        ):
            raise ValueError("Evidence requires unambiguous public/historical source IDs")
        lookup[source.id] = source.text
    invalid = [
        f"{cite.source_id}: {cite.quote[:150]!r}"
        for cite in citations
        if cite.source_id not in lookup or cite.quote not in lookup[cite.source_id]
    ]
    if invalid:
        raise ValueError(
            "Citation is absent from supplied evidence; copy exact substrings: "
            + "; ".join(invalid)
        )


class Claim(BaseModel):
    text: str
    support: Literal["explicit", "inferred"]
    evidence: list[Citation] = Field(min_length=1)


class RecordInsights(BaseModel):
    """Evidence supports what was stated; it does not prove a real-world action occurred."""

    model_config = ConfigDict(extra="forbid")
    summary: str
    goals: list[Claim] = Field(default_factory=list)
    facts: list[Claim] = Field(default_factory=list)
    reported_actions: list[Claim] = Field(default_factory=list)
    conversation_functions: list[Claim] = Field(default_factory=list)
    exception_candidates: list[Claim] = Field(default_factory=list)
    missing_information: list[str] = Field(default_factory=list)

    def check_sources(self, sources: list[EvidenceText]) -> None:
        claims = chain(
            self.goals,
            self.facts,
            self.reported_actions,
            self.conversation_functions,
            self.exception_candidates,
        )
        check_citations((cite for claim in claims for cite in claim.evidence), sources)


class ProcedureStep(BaseModel):
    action: str
    tool: str | None = None
    condition: str
    evidence: list[Citation] = Field(min_length=1)


class ProcedureDraft(BaseModel):
    model_config = ConfigDict(extra="forbid")
    status: Literal["draft"] = "draft"
    intent: str
    required_information: list[str]
    steps: list[ProcedureStep]
    stop_conditions: list[str]
    verified_outcome: str

    def check_sources(self, policies: list[EvidenceText], allowed_tools: list[str]) -> None:
        if not policies or any(p.role != "public" for p in policies):
            raise ValueError("Procedure drafts require explicit public policy sources")
        check_citations((cite for step in self.steps for cite in step.evidence), policies)
        for step in self.steps:
            if step.tool is not None and step.tool not in allowed_tools:
                raise ValueError(f"Procedure names an unavailable tool: {step.tool}")
