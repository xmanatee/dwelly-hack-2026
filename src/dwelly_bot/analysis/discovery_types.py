"""Analyst-only discovery artifacts; no inferred taxonomy or procedure grants authority."""

from itertools import chain
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from dwelly_bot.context.evidence import Citation, EvidenceText, check_citations

type SourceKind = Literal["question", "conversation", "policy", "document"]
type IssueKind = Literal[
    "missing_information",
    "contradiction",
    "verification_failure",
    "procedural_exception",
    "complaint",
    "fraud_security",
    "financial_harm",
    "irreversible_action",
    "support_need",
    "multi_intent",
    "unclear_intent",
    "deadline",
    "unusual_outcome",
    "policy_gap",
]


class DiscoveryRecord(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: str
    title: str
    kind: SourceKind
    sources: list[EvidenceText]
    domain: str = ""

    def text(self) -> str:
        return "\n".join(s.text for s in self.sources)


class Finding(BaseModel):
    category: IssueKind
    description: str = Field(max_length=400)
    scope: Literal["observed_case", "scenario", "policy_rule", "hypothesis"]
    priority: Literal["review", "high"]
    evidence: list[Citation] = Field(min_length=1)
    next_check: str = Field(max_length=400)


class ScreenedRecord(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: str
    summary: str = Field(max_length=500)
    domain: str
    topic: str = Field(max_length=120)
    secondary_topics: list[str] = Field(default_factory=list, max_length=3)
    goal: str | None = None
    action: str | None = None
    outcome: Literal[
        "resolved",
        "partial",
        "awaiting_customer",
        "escalated",
        "rejected",
        "unresolved",
        "unknown",
        "not_available",
    ]
    reported_handling: list[str] = Field(default_factory=list, max_length=5)
    required_information: list[str] = Field(default_factory=list, max_length=6)
    findings: list[Finding] = Field(default_factory=list, max_length=5)
    evidence: list[Citation] = Field(min_length=1, max_length=4)

    def check(self, record: DiscoveryRecord) -> None:
        if self.id != record.id:
            raise ValueError("Screening returned a different record ID")
        check_citations(chain(self.evidence, *(f.evidence for f in self.findings)), record.sources)
        if record.kind != "conversation":
            if self.outcome != "not_available" or self.reported_handling:
                raise ValueError(
                    "Non-conversation sources cannot contain observed customer handling"
                )
            if any(f.scope == "observed_case" for f in self.findings):
                raise ValueError("A document, policy or question is not an observed customer case")
        if record.kind in {"question", "document"} and any(
            f.scope == "policy_rule" for f in self.findings
        ):
            raise ValueError(
                "Question/document findings must be scenario/hypothesis, not an established policy rule"
            )


class ScreenBatch(BaseModel):
    records: list[ScreenedRecord]


class IntentDefinition(BaseModel):
    id: str = Field(pattern=r"^[a-z][a-z0-9_.-]+$")
    parent: str
    name: str
    definition: str = Field(max_length=500)
    aliases: list[str]
    inclusion: str
    exclusion: str
    representative_ids: list[str]
    counterexample_ids: list[str] = Field(default_factory=list)
    unresolved_questions: list[str] = Field(default_factory=list)


class TaxonomyDraft(BaseModel):
    status: Literal["draft"] = "draft"
    intents: list[IntentDefinition]
    unmapped_aliases: list[str] = Field(default_factory=list)
    assignment_errors: list[str] = Field(default_factory=list)


class CrossConflict(BaseModel):
    record_ids: list[str] = Field(min_length=1)
    description: str
    status: Literal["potential_conflict", "scope_difference", "internal_inconsistency"]
    evidence: list[Citation] = Field(min_length=2)
    next_check: str

    def check(self, records: list[DiscoveryRecord]) -> None:
        lookup = {record.id: record for record in records}
        ids = set(self.record_ids)
        internal = self.status == "internal_inconsistency"
        if (
            ids - lookup.keys()
            or len(ids) != len(self.record_ids)
            or len(ids) != (1 if internal else 2)
        ):
            raise ValueError(
                "Conflicts require one internal record or two distinct supplied records"
            )
        sources = [source for id in ids for source in lookup[id].sources]
        check_citations(self.evidence, sources, unique=False)
        cited = {cite.source_id for cite in self.evidence}
        if any(not cited.intersection(source.id for source in lookup[id].sources) for id in ids):
            raise ValueError("Every conflict record needs supporting citations")
        if len({(cite.source_id, cite.quote) for cite in self.evidence}) < 2:
            raise ValueError("Conflicts require two distinct evidence quotations")


class ConflictBatch(BaseModel):
    conflicts: list[CrossConflict]


class ObservedPattern(BaseModel):
    intent_id: str
    case_ids: list[str] = Field(min_length=2)
    steps: list[str]
    negative_paths: list[str]
    unknown_checks: list[str]
    evidence: list[Citation] = Field(min_length=2)
    status: Literal["observed_pattern"] = "observed_pattern"

    def check(self, records: list[DiscoveryRecord]) -> None:
        lookup = {record.id: record for record in records}
        if len(set(self.case_ids)) != len(self.case_ids) or set(self.case_ids) - lookup.keys():
            raise ValueError("Handling patterns require distinct supplied cases of the same intent")
        sources = [source for id in self.case_ids for source in lookup[id].sources]
        check_citations(self.evidence, sources, unique=False)
        cited = {cite.source_id for cite in self.evidence}
        if any(not cited.intersection(s.id for s in lookup[id].sources) for id in self.case_ids):
            raise ValueError("Every pattern case needs supporting citations")


class PatternBatch(BaseModel):
    patterns: list[ObservedPattern]


class AuditRecord(BaseModel):
    id: str
    decision: Literal["supported", "needs_revision", "missed_issue", "unknown"]
    issue: Finding | None = None
    reason: str
    evidence: list[Citation]


class AuditBatch(BaseModel):
    records: list[AuditRecord]
