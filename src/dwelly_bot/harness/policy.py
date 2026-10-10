"""Reviewed deterministic risk rules; a hint classifier never establishes safety."""

import json
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class RiskRule(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: str
    terms: list[str] = Field(min_length=1)
    handling: Literal["flag", "needs_info", "human_review"]
    reason: str


class PolicyGate:
    def __init__(self, inputs: dict[str, Any], rules: list[RiskRule]) -> None:
        text = json.dumps(inputs, ensure_ascii=False).casefold()
        self.matches = [
            {
                "rule": r.id,
                "handling": r.handling,
                "reason": r.reason,
                "matched_terms": [t for t in r.terms if t.casefold() in text],
            }
            for r in rules
            if any(t.casefold() in text for t in r.terms)
        ]

    def classify(self) -> dict[str, Any]:
        return {"flags": self.matches, "reviewed_rules_only": True, "unmatched_is_safe": False}

    def guard(self, name: str, read_only: bool) -> None:
        if (
            not read_only
            and name != "escalate_case"
            and any(r["handling"] in {"human_review", "needs_info"} for r in self.matches)
        ):
            raise ValueError("Reviewed policy requires clarification or human review before writes")
