"""Provisional executor interface and explicit offline action receipts."""

from typing import Literal, Protocol

from pydantic import BaseModel, Field

from dwelly_bot.channels.intake import Contract, Trigger
from dwelly_bot.experiments.journal import Journal


class ActionReceipt(Contract):
    action_id: str
    status: Literal["simulated", "computed", "failed", "skipped"]
    operation: str
    target: str
    detail: str
    parameters: dict[str, str] = Field(default_factory=dict)
    replayed: bool = False
    outputs: dict[str, str] = Field(default_factory=dict)


class ExecutionResult(Contract):
    event_id: str
    mode: Literal["mock"] = "mock"
    status: Literal["simulated", "failed", "empty"]
    disposition: str
    receipts: tuple[ActionReceipt, ...]


class Executor[PlanT: BaseModel](Protocol):
    @property
    def capabilities(self) -> str: ...

    async def execute(self, trigger: Trigger, plan: PlanT, journal: Journal) -> ExecutionResult: ...
