"""Local model receipts and explicit processing-failure outputs."""

from pydantic import BaseModel

from dwelly_bot.harness.runtime import CaseRuntime
from dwelly_bot.models import BudgetedModel
from hackathon_winner.generation import Generated


class PlannerFailure(BaseModel):
    status: str = "error"
    error: str


def failure_notice(stage: str, error: str) -> Generated:
    return Generated(
        answer="Processing could not be completed; this case requires human review.",
        reasoning=f"{stage} error: {error}",
    )


def record_trace(runtime: CaseRuntime, models: list[BudgetedModel]) -> None:
    runtime.journal.append(
        {
            "kind": "model_trace",
            "config": runtime.config.model_dump(mode="json"),
            "roles": runtime.role_records,
            "costs": [c for model in models for c in model.calls],
        }
    )
