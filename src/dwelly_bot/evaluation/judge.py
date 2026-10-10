"""Bounded, read-only model judge over saved evidence; no tools or exporters."""

# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

import asyncio
import json
import time
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict
from pydantic_ai import Agent
from pydantic_ai.models import Model
from pydantic_ai.settings import ModelSettings
from pydantic_ai.usage import UsageLimits

from dwelly_bot.budget import BudgetLedger
from dwelly_bot.contracts import ModelProfile
from dwelly_bot.models import BudgetedModel
from dwelly_bot.resources import text

ROOT = Path(__file__).parent


class InvalidReview(ValueError):
    def __init__(self, message: str, record: dict[str, Any]):
        super().__init__(message)
        self.record = record


class Finding(BaseModel):
    model_config = ConfigDict(extra="forbid")
    criterion: str
    status: Literal["pass", "fail", "unknown"]
    reason: str
    evidence_ids: list[str]


class JudgeResult(BaseModel):
    model_config = ConfigDict(extra="forbid")
    summary: str
    findings: list[Finding]


def evidence_pack(case: dict[str, Any], rubric: dict[str, Any]) -> dict[str, Any]:
    """Keep reference labels/raw benchmark metadata out of the judge context."""
    records = {
        "TASK": case.get("input"),
        "ANSWER": case.get("answer"),
        "RATIONALE": case.get("public_rationale"),
        "EXECUTION": {"status": case.get("execution_status"), "error": case.get("error")},
    }
    for i, event in enumerate(case.get("tool_events", []), 1):
        records[f"T{i}"] = event
    for phase, snapshot in case.get("state_snapshots", {}).items():
        records["STATE-" + phase.upper()] = snapshot
    for i, source in enumerate(case.get("sources", []), 1):
        records[f"SOURCE-{i}"] = source
    return {"criteria": rubric["criteria"], "evidence": records}


class LlmJudge:
    def __init__(
        self,
        model: Model,
        rubric: dict[str, Any],
        *,
        instructions: str | None = None,
        timeout: float = 45,
        settings: ModelSettings | None = None,
        ledger: BudgetLedger | None = None,
        profile: ModelProfile | None = None,
    ) -> None:
        self.rubric, self.timeout = rubric, timeout
        self.model, self.settings, self.ledger, self.profile = model, settings, ledger, profile
        self.instructions = instructions or text("prompts/judge.md")
        self.agent: Agent[None, JudgeResult] = Agent(
            model,
            output_type=JudgeResult,
            model_settings=settings,
            instructions=self.instructions,
        )

        self.agent.instrument = False

    async def review(self, case: dict[str, Any]) -> dict[str, Any]:
        payload = evidence_pack(case, self.rubric)
        start = time.monotonic()
        bounded = (
            BudgetedModel(
                self.model, self.ledger, "judge/" + case["id"], self.timeout, profile=self.profile
            )
            if self.ledger
            else None
        )
        try:
            with self.agent.override(model=bounded or self.model):
                result = await asyncio.wait_for(
                    self.agent.run(
                        json.dumps(payload, ensure_ascii=False),
                        usage_limits=UsageLimits(request_limit=2),
                    ),
                    timeout=self.timeout,
                )
        except Exception as error:
            raise InvalidReview(
                f"Judge request failed ({type(error).__name__})",
                {"input_payload": payload, "cost_records": bounded.calls if bounded else []},
            ) from None
        return validated_review(
            result.output,
            payload,
            self.rubric,
            metrics={
                "elapsed_ms": round((time.monotonic() - start) * 1000, 2),
                "input_tokens": result.usage.input_tokens,
                "output_tokens": result.usage.output_tokens,
                "requests": result.usage.requests,
                "cost_usd": sum(c["cost_usd"] for c in bounded.calls if c["status"] == "settled")
                if bounded and all(c["status"] == "settled" for c in bounded.calls)
                else None,
                "cost_records": bounded.calls if bounded else [],
            },
        )


def review_fields(review: dict[str, Any]) -> dict[str, Any]:
    """Publish the same saved assessment contract for live and batch judging."""
    return {
        "judge_status": review["status"],
        "judge": review["findings"],
        "judge_summary": review["summary"],
        "judge_metrics": review["metrics"],
        "judge_record": {key: review[key] for key in ("input_payload", "raw_output")},
    }


def validated_review(
    output: JudgeResult,
    payload: dict[str, Any],
    rubric: dict[str, Any],
    *,
    metrics: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Same evidence/schema checks for synchronous and asynchronous batch reviews."""
    record = {"input_payload": payload, "raw_output": output.model_dump(), "metrics": metrics or {}}
    expected = [c["id"] for c in rubric["criteria"]]
    ids = [f.criterion for f in output.findings]
    if len(ids) != len(set(ids)) or set(ids) != set(expected):
        raise InvalidReview("LlmJudge omitted, duplicated or invented a criterion", record)
    for finding in output.findings:
        if not finding.reason.strip() or not finding.evidence_ids:
            raise InvalidReview(
                "LlmJudge returned a verdict without a reason/evidence references", record
            )
        if set(finding.evidence_ids) - set(payload["evidence"]):
            raise InvalidReview("LlmJudge cited nonexistent evidence IDs", record)
    labels = {c["id"]: c["label"] for c in rubric["criteria"]}
    return {
        "status": "available",
        "summary": output.summary,
        **record,
        "findings": [dict(f.model_dump(), label=labels[f.criterion]) for f in output.findings],
    }
