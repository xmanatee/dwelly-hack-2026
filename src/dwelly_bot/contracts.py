"""Public agent contract and isolated dataset adapter boundary."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Any, Literal, Protocol

from pydantic import BaseModel, ConfigDict, Field, model_validator

type JsonRecord = dict[str, Any]
type Subject = Callable[[JsonRecord, "Journal"], Awaitable[JsonRecord]]
type StateReader = Callable[[], JsonRecord | Awaitable[JsonRecord]]

if TYPE_CHECKING:
    from dwelly_bot.experiments.journal import Journal
    from dwelly_bot.harness.runtime import CaseRuntime


class SolutionOutput(BaseModel):
    answer: str
    public_rationale: str = Field(
        description="Short explanation with observed evidence; no hidden reasoning"
    )
    agent_disposition: Literal["completed", "needs_info", "escalated", "refused"] = "completed"


class CheckResult(BaseModel):
    model_config = ConfigDict(extra="allow", strict=True)
    id: str = Field(min_length=1)
    status: Literal["pass", "fail", "unknown"]
    label: str | None = None
    reason: str | None = None
    dimension: str = "dataset"


class Verification(BaseModel):
    model_config = ConfigDict(extra="allow", strict=True)
    status: Literal["available", "unavailable", "error"]
    goal_pass: bool | None = None
    checks: list[CheckResult] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_result(self) -> Verification:
        if self.status != "available" and self.goal_pass is not None:
            raise ValueError("Unavailable verification cannot declare a goal verdict")
        ids = [check.id for check in self.checks]
        if len(set(ids)) != len(ids):
            raise ValueError("Verification check IDs must be unique")
        return self


class Modules(BaseModel):
    """Optional capabilities; authority checks and execution journaling are always enabled."""

    model_config = ConfigDict(extra="forbid")
    knowledge: bool = True
    calculator: bool = True


class ModelProfile(BaseModel):
    """Public model settings; credentials are environment-variable names only."""

    model_config = ConfigDict(extra="forbid", hide_input_in_errors=True, allow_inf_nan=False)
    model: str = "openai/gpt-4.1-mini"
    provider: Literal["openrouter", "openai", "anthropic"] = "openrouter"
    key_envs: list[str] = Field(default_factory=list)
    account_budget_usd: float = Field(default=100, gt=0, le=10000)
    input_price_per_million: float | None = Field(default=None, gt=0)
    output_price_per_million: float | None = Field(default=None, gt=0)
    provider_only: list[str] = Field(default_factory=list)
    provider_sort: Literal["price", "latency", "throughput"] = "latency"
    tool_choice_required: bool = True
    anthropic_cache: bool = False
    reasoning_enabled: bool = False
    max_tokens: int = Field(default=2048, ge=256, le=128000)
    reasoning_effort: Literal["none", "minimal", "low", "medium", "high", "xhigh", "max"] | None = (
        None
    )

    @model_validator(mode="after")
    def validate_transport(self) -> ModelProfile:
        if self.anthropic_cache and self.provider != "anthropic":
            raise ValueError("anthropic_cache requires the direct Anthropic provider")
        if self.provider != "openrouter" and (
            self.input_price_per_million is None or self.output_price_per_million is None
        ):
            raise ValueError("Direct providers require explicit input/output token price ceilings")
        if any(not name.isidentifier() for name in self.key_envs):
            raise ValueError("key_envs must contain environment-variable names, never credentials")
        if len(self.key_envs) != len(set(self.key_envs)):
            raise ValueError("Duplicate credential environment-variable names")
        if self.provider == "anthropic" and self.reasoning_effort in {"none", "minimal", "xhigh"}:
            raise ValueError("Anthropic effort must be low, medium, high or max")
        if self.provider == "openrouter" and self.reasoning_effort == "max":
            raise ValueError("OpenRouter effort uses xhigh rather than max")
        return self


class PlannerConfig(BaseModel):
    """Separately tunable decision planner; no tools. The advisory mode name is retained for config compatibility."""

    model_config = ConfigDict(extra="forbid")
    mode: Literal["off", "advisory"] = "advisory"
    # None reuses the solver's model, account and limits.
    model: ModelProfile | None = None
    # planner/playbooks/<name>.md (prose) and <name>.json (actions and safety flags).
    playbook: str = Field(default="banking", pattern=r"^[a-z0-9_-]+$")
    skill_selection: Literal["model", "all"] = "model"
    instructions: str = Field(default="", max_length=16000)


class RunConfig(ModelProfile):
    max_requests: int = Field(default=40, ge=1, le=100)
    max_tool_calls: int = Field(default=80, ge=1, le=200)
    max_tool_result_bytes: int = Field(default=32768, ge=256, le=131072)
    tool_timeout_seconds: float = Field(default=10, ge=0.001, le=120)
    max_total_tokens: int = Field(default=350000, ge=1, le=2000000)
    max_input_tokens: int = Field(default=90000, ge=1, le=200000)
    case_timeout_seconds: float = Field(default=240, ge=10, le=3600)
    request_timeout_seconds: float = Field(default=60, ge=5, le=900)
    total_budget_usd: float = Field(default=15, gt=0, le=10000)
    budget_file: str | None = None
    skills: list[str] = Field(default_factory=list)
    skill_mode: Literal["preload", "on_demand"] = "preload"
    domain_skill_enabled: bool = True
    disabled_tools: list[str] = Field(default_factory=list)
    case_concurrency: int = Field(default=1, ge=1, le=32)
    run_timeout_seconds: float = Field(default=1800, gt=0, le=86400)
    deadline_utc: str | None = None
    environment_state_mode: Literal["isolated", "shared"] = "isolated"
    retries: int = Field(default=1, ge=0, le=2)
    modules: Modules = Field(default_factory=Modules)
    instructions: str = Field(default="", max_length=16000)
    planner: PlannerConfig | None = None

    @model_validator(mode="after")
    def validate_run(self) -> RunConfig:
        if self.environment_state_mode == "shared" and self.case_concurrency != 1:
            raise ValueError("Shared external worlds require sequential cases")
        if self.total_budget_usd > 15 and not self.budget_file:
            raise ValueError("Budgets above $15 require an explicit budget_file")
        if self.deadline_utc:
            from datetime import datetime

            stamp = datetime.fromisoformat(self.deadline_utc.replace("Z", "+00:00"))
            if stamp.tzinfo is None:
                raise ValueError("deadline_utc requires an explicit timezone")
        return self


@dataclass
class AgentCase:
    id: str
    dataset: str
    title: str
    input: dict[str, Any]
    metadata: dict[str, Any] = field(default_factory=dict, repr=False)
    sources: list[str] = field(default_factory=list)


class CaseSession(Protocol):
    async def run(self, runtime: CaseRuntime) -> SolutionOutput: ...

    def snapshot(self) -> dict[str, Any]: ...


class DatasetAdapter(Protocol):
    name: str
    dataset_root: Path

    @property
    def state_mode(self) -> Literal["static", "isolated", "shared"]: ...

    def load_cases(self, root: Path, ids: list[str] | None = None) -> list[AgentCase]: ...

    def prepare(self, case: AgentCase, root: Path, config: RunConfig) -> CaseSession: ...

    def grade_saved(
        self, case: AgentCase, root: Path, config: RunConfig, execution: dict[str, Any]
    ) -> dict[str, Any]: ...
