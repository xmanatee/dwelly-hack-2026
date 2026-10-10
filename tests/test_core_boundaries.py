"""The common pipeline preserves failures and applies identical tool constraints."""

import asyncio
import time
from collections.abc import Awaitable, Callable
from pathlib import Path
from typing import Any, cast

import pytest
from pydantic_ai.exceptions import ModelRetry
from pydantic_ai.messages import ModelResponse, ToolCallPart
from pydantic_ai.models.function import FunctionModel
from pydantic_ai.models.test import TestModel

from dwelly_bot.budget import BudgetExceeded, BudgetLedger
from dwelly_bot.contracts import AgentCase, DatasetAdapter, RunConfig, SolutionOutput
from dwelly_bot.experiments.agent import capture_cases
from dwelly_bot.experiments.journal import Journal, capture_case
from dwelly_bot.harness.runtime import CaseRuntime, StatefulToolResultTooLarge
from dwelly_bot.storage import load_json


class LocalSession:
    async def run(self, runtime: CaseRuntime) -> SolutionOutput:
        return SolutionOutput(answer="recorded", public_rationale="Local capture boundary probe")

    def snapshot(self) -> dict[str, Any]:
        return {"read_only": True}

    def grade(self, execution: dict[str, Any]) -> dict[str, Any]:
        raise AssertionError("Capture must not run an evaluator")


class BrokenAdapter:
    name = "fixture"
    state_mode = "static"

    def prepare(self, case: AgentCase, root: Path, config: RunConfig) -> LocalSession:
        if case.id == "bad":
            raise ValueError("Malformed fixture")
        return LocalSession()


def fixture(tmp_path: Path) -> tuple[list[AgentCase], dict[str, Any]]:
    cases = [AgentCase(id=key, dataset="fixture", title=key, input={}) for key in ["bad", "good"]]
    bundle = {
        "schema_version": 1,
        "runs": [
            {"id": "fixture", "cases": [], "manifest": {"assigned_case_ids": [c.id for c in cases]}}
        ],
    }
    return cases, bundle


async def test_preparation_error_is_captured_and_next_case_runs(tmp_path: Path) -> None:
    cases, bundle = fixture(tmp_path)
    await capture_cases(
        cast(DatasetAdapter, BrokenAdapter()),
        tmp_path,
        cases,
        RunConfig(),
        TestModel(),
        BudgetLedger(tmp_path / "global-budget.json"),
        tmp_path,
        bundle,
    )
    saved = load_json(tmp_path / "results.json.gz")["runs"][0]["cases"]
    assert [r["execution_status"] for r in saved] == ["error", "completed"]
    assert "Malformed fixture" in saved[0]["error"]


async def test_readonly_timeout_returns_without_blocking_event_loop(tmp_path: Path) -> None:
    journal = Journal(tmp_path / "tools.jsonl")
    runtime = CaseRuntime(TestModel(), RunConfig(tool_timeout_seconds=0.005), journal)

    def slow_read() -> str:
        time.sleep(0.04)
        return "late read"

    tool = runtime.tool("slow_read", "Read only", slow_read, read_only=True)
    started = time.monotonic()
    with pytest.raises(ModelRetry, match="TimeoutError"):
        await cast(Callable[[], Awaitable[Any]], tool.function)()
    assert time.monotonic() - started < 0.035
    assert journal.events[0]["status"] == "error"
    await asyncio.sleep(0.05)
    journal.close()


async def test_tool_result_cap_records_failure_before_model_context(tmp_path: Path) -> None:
    journal = Journal(tmp_path / "tools.jsonl")
    runtime = CaseRuntime(TestModel(), RunConfig(max_tool_result_bytes=256), journal)

    def large_read() -> str:
        return "x" * 1000

    tool = runtime.tool("large_read", "Large read", large_read, read_only=True)
    with pytest.raises(ModelRetry, match="byte limit"):
        await cast(Callable[[], Awaitable[Any]], tool.function)()
    assert journal.events[0]["status"] == "error"
    assert "result" not in journal.events[0]
    journal.close()


async def test_oversized_action_response_never_repeats_mutation(tmp_path: Path) -> None:
    journal = Journal(tmp_path / "tools.jsonl")
    effects = 0
    requests = 0

    def mutate() -> str:
        nonlocal effects
        effects += 1
        return "x" * 1000

    def model(messages: Any, info: Any) -> ModelResponse:
        nonlocal requests
        requests += 1
        return ModelResponse(parts=[ToolCallPart("mutate", {})])

    runtime = CaseRuntime(
        FunctionModel(model), RunConfig(max_tool_result_bytes=256, retries=2), journal
    )
    agent = runtime.agent(
        output_type=SolutionOutput,
        output_name="answer",
        tools=[runtime.tool("mutate", "Change state", mutate)],
        instructions="Perform the requested action",
    )
    with pytest.raises(StatefulToolResultTooLarge, match="without retry"):
        await runtime.ask(agent, "Change state")
    assert effects == requests == 1
    assert journal.events[0]["status"] == "error"
    assert "response_sha256" in journal.events[0]["error"]["message"]
    journal.close()


async def test_cancellation_keeps_current_capture_and_assigned_remainder(tmp_path: Path) -> None:
    entered = asyncio.Event()

    class WaitingSession(LocalSession):
        async def run(self, runtime: CaseRuntime) -> SolutionOutput:
            runtime.role_records.append({"role": "subject", "messages": []})
            runtime.usage.requests = 1
            token = runtime.model.ledger.reserve_account(0.1, "fixture", "cancelled")[0]
            runtime.model.ledger.uncertain(token)
            runtime.model.calls.append({"status": "uncertain", "reserved_usd": 0.1})
            entered.set()
            await asyncio.sleep(10)
            raise AssertionError("unreachable")

    class WaitingAdapter(BrokenAdapter):
        def prepare(self, case: AgentCase, root: Path, config: RunConfig) -> WaitingSession:
            return WaitingSession()

    cases, bundle = fixture(tmp_path)
    task = asyncio.create_task(
        capture_cases(
            cast(DatasetAdapter, WaitingAdapter()),
            tmp_path,
            cases,
            RunConfig(),
            TestModel(),
            BudgetLedger(tmp_path / "global-budget.json"),
            tmp_path,
            bundle,
        )
    )
    await entered.wait()
    task.cancel()
    with pytest.raises(asyncio.CancelledError):
        await task
    rows = load_json(tmp_path / "results.json.gz")["runs"][0]["cases"]
    assert [r["execution_status"] for r in rows] == ["cancelled", "not_started"]
    assert rows[0]["usage"]["requests"] == 1
    assert rows[0]["metrics"]["cost_usd"] is None
    assert rows[0]["metrics"]["unconfirmed_exposure_usd"] == 0.1
    assert rows[0]["model_roles"][0]["role"] == "subject"
    assert rows[0]["model_costs"][0]["status"] == "uncertain"


async def test_agent_recovers_from_a_failed_read(tmp_path: Path) -> None:
    calls = 0

    def read() -> str:
        nonlocal calls
        calls += 1
        if calls == 1:
            raise FileNotFoundError("Evidence temporarily unavailable")
        return "verified evidence"

    def model(messages: Any, info: Any) -> ModelResponse:
        if calls < 2:
            return ModelResponse([ToolCallPart("read", {})])
        return ModelResponse(
            [
                ToolCallPart(
                    info.output_tools[0].name,
                    {"answer": "done", "public_rationale": "verified evidence"},
                )
            ]
        )

    journal = Journal(tmp_path / "tools.jsonl")
    runtime = CaseRuntime(FunctionModel(model), RunConfig(), journal)
    agent = runtime.agent(
        output_type=SolutionOutput,
        output_name="finish",
        instructions="Read evidence",
        tools=[runtime.tool("read", "Read", read, read_only=True)],
    )
    result = await runtime.ask(agent, "Read the evidence")
    journal.close()
    assert result.output.answer == "done" and runtime.usage.requests == 3
    assert [event["status"] for event in journal.events] == ["error", "returned"]


@pytest.mark.parametrize(
    "error,reason", [(BudgetExceeded("limit"), "budget"), (TimeoutError(), "timeout")]
)
async def test_resource_stops_are_not_business_decisions(
    tmp_path: Path, error: Exception, reason: str
) -> None:
    async def subject(inputs: Any, journal: Any) -> Any:
        raise error

    case = await capture_case({"id": "A", "input": {}}, tmp_path / "case", subject)
    assert case["stop_reason"] == reason and case["execution_status"] == "error"
    assert "answer" not in case and "agent_disposition" not in case
    from dwelly_bot.reporting.submission import export

    export(
        {
            "schema_version": 1,
            "runs": [{"id": "test", "manifest": {"assigned_case_ids": ["A"]}, "cases": [case]}],
        },
        tmp_path / "answers",
    )
    assert "requires human review" in (tmp_path / "answers/1/ANSWER.md").read_text()
