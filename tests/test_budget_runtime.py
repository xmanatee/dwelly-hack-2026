"""Budget/cancellation/tool capture contracts, without network or model credits."""

import json
from concurrent.futures import ThreadPoolExecutor
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest
from pydantic_ai import Agent
from pydantic_ai.messages import ModelResponse, TextPart, ToolCallPart
from pydantic_ai.models.function import AgentInfo, FunctionModel
from pydantic_ai.usage import RequestUsage

from dwelly_bot.budget import BudgetExceeded, BudgetLedger
from dwelly_bot.contracts import RunConfig
from dwelly_bot.experiments.journal import Journal
from dwelly_bot.harness.runtime import CaseRuntime
from dwelly_bot.models import BudgetedModel


def test_shared_ceiling_counts_unconfirmed_calls(tmp_path: Path) -> None:
    ledger = BudgetLedger(tmp_path / "budget.json", 1)
    token = ledger.reserve_account(0.6, "test", "one")[0]
    ledger.uncertain(token)
    with pytest.raises(BudgetExceeded):
        ledger.reserve_account(0.4, "test", "retry")
    assert ledger.summary()["uncertain_requests"] == 1
    ledger.settle(token, 0.05, "provider_reported", "fake-test-response")
    ledger.reserve_account(0.4, "test", "next")
    assert ledger.summary()["reported_cost_usd"] == 0.05


def test_ceiling_cannot_be_raised_by_new_process(tmp_path: Path) -> None:
    first = BudgetLedger(tmp_path / "budget.json", 0.5)
    first.reserve_account(0.3, "test", "one")
    with pytest.raises(BudgetExceeded):
        BudgetLedger(tmp_path / "budget.json", 15).reserve_account(0.3, "test", "two")
    with pytest.raises(ValueError):
        RunConfig(total_budget_usd=16)
    assert RunConfig(total_budget_usd=16, budget_file="other.json").total_budget_usd == 16


def test_parallel_reservations_cannot_overrun(tmp_path: Path) -> None:
    def reserve(_: int) -> bool:
        try:
            BudgetLedger(tmp_path / "budget.json", 5).reserve_account(1, "test", "one")
            return True
        except BudgetExceeded:
            return False

    with ThreadPoolExecutor(max_workers=8) as pool:
        assert sum(pool.map(reserve, range(20))) == 4
    assert BudgetLedger(tmp_path / "budget.json", 5).summary()["exposure_usd"] == 4


async def test_real_sdk_tool_and_cost_capture(tmp_path: Path, journal: Journal) -> None:
    calls = 0

    def model(_: Any, info: AgentInfo) -> ModelResponse:
        nonlocal calls
        calls += 1
        if calls == 1:
            return ModelResponse(
                parts=[ToolCallPart("add", {"a": 2, "b": 3})],
                provider_details={"cost": 0.002},
                usage=RequestUsage(input_tokens=30, output_tokens=5, cost=Decimal("0.002")),
            )
        return ModelResponse(
            parts=[TextPart("5")],
            provider_details={"cost": 0.003},
            usage=RequestUsage(input_tokens=40, output_tokens=2, cost=Decimal("0.003")),
        )

    ledger = BudgetLedger(tmp_path / "budget.json", 1)
    wrapped = BudgetedModel(FunctionModel(model), ledger, "scripted")
    runtime = CaseRuntime(wrapped, RunConfig(), journal)

    def add(a: int, b: int) -> int:
        return a + b

    agent = Agent(model=wrapped, tools=[runtime.tool("add", "Add numbers", add)])
    agent.instrument = False
    result = await runtime.ask(agent, "Add two and three")
    assert result.output == "5"
    assert journal.events[0]["result"] == 5
    assert ledger.summary()["reported_cost_usd"] == 0.005
    assert len(runtime.role_records) == 1
    assert json.loads(json.dumps(wrapped.calls))[0]["usage"]["cost"] == "0.002"


async def test_failed_request_keeps_reservation(tmp_path: Path) -> None:
    def failed(_: Any, info: AgentInfo) -> ModelResponse:
        raise TimeoutError("upstream acknowledgement missing")

    ledger = BudgetLedger(tmp_path / "budget.json", 1)
    agent = Agent(model=BudgetedModel(FunctionModel(failed), ledger, "error"))
    with pytest.raises(TimeoutError):
        await agent.run("test")
    assert ledger.summary()["uncertain_requests"] == 1
    assert ledger.summary()["exposure_usd"] > 0


async def test_billing_details_override_catalog_estimate(tmp_path: Path) -> None:
    def response(_: Any, info: AgentInfo) -> ModelResponse:
        return ModelResponse(
            parts=[TextPart("done")],
            usage=RequestUsage(cost=Decimal("0.001")),
            provider_details={"cost": 0.003},
        )

    ledger = BudgetLedger(tmp_path / "budget.json", 1)
    await Agent(model=BudgetedModel(FunctionModel(response), ledger, "priced")).run("test")
    assert ledger.summary()["reported_cost_usd"] == 0.003


async def test_instruction_bytes_are_reserved_before_request(tmp_path: Path) -> None:
    invoked = False

    def response(_: Any, info: AgentInfo) -> ModelResponse:
        nonlocal invoked
        invoked = True
        return ModelResponse(parts=[TextPart("done")])

    ledger = BudgetLedger(tmp_path / "budget.json", 0.03)
    agent = Agent(
        model=BudgetedModel(FunctionModel(response), ledger, "long"), instructions="x" * 50000
    )
    with pytest.raises(BudgetExceeded):
        await agent.run("test")
    assert invoked is False


async def test_wall_timeout_keeps_uncertain_exposure(tmp_path: Path) -> None:
    import asyncio

    async def response(_: Any, info: AgentInfo) -> ModelResponse:
        await asyncio.sleep(10)
        return ModelResponse(parts=[TextPart("unreachable")])

    ledger = BudgetLedger(tmp_path / "budget.json", 1)
    wrapped = BudgetedModel(FunctionModel(response), ledger, "slow", request_timeout=0.01)
    with pytest.raises(TimeoutError):
        await Agent(model=wrapped).run("test")
    assert ledger.summary()["uncertain_requests"] == 1


async def test_anthropic_cache_pricing_and_request_settings(tmp_path: Path) -> None:
    from dwelly_bot.contracts import ModelProfile

    def response(_: Any, info: AgentInfo) -> ModelResponse:
        assert info.model_settings is not None
        assert info.model_settings.get("anthropic_cache") == "5m"
        return ModelResponse(
            parts=[TextPart("done")],
            usage=RequestUsage(
                input_tokens=600, cache_write_tokens=200, cache_read_tokens=300, output_tokens=10
            ),
        )

    ledger = BudgetLedger(tmp_path / "budget.json", 1)
    profile = ModelProfile(
        model="claude-sonnet-5-5",
        provider="anthropic",
        anthropic_cache=True,
        input_price_per_million=2,
        output_price_per_million=10,
    )
    await Agent(model=BudgetedModel(FunctionModel(response), ledger, "cache", profile=profile)).run(
        "test"
    )
    assert ledger.summary()["exposure_usd"] == pytest.approx(0.00086)


async def test_openrouter_structured_output_without_forced_tool_choice(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import httpx2 as httpx
    from openai import AsyncOpenAI

    from dwelly_bot.contracts import ModelProfile, SolutionOutput
    from dwelly_bot.providers import model_context

    def respond(request: httpx.Request) -> httpx.Response:
        body = json.loads(request.content)
        assert body["tool_choice"] == "auto"
        function = {
            "name": body["tools"][0]["function"]["name"],
            "arguments": json.dumps({"answer": "done", "public_rationale": "fixture"}),
        }
        call = {"id": "call_fixture", "type": "function", "function": function}
        message = {"role": "assistant", "tool_calls": [call]}
        choice = {"index": 0, "finish_reason": "tool_calls", "message": message}
        return httpx.Response(
            200,
            json={
                "id": "fixture",
                "object": "chat.completion",
                "provider": "Minimax",
                "created": 0,
                "model": "minimax/minimax-m3",
                "choices": [choice],
            },
        )

    client = AsyncOpenAI(
        api_key="offline", http_client=httpx.AsyncClient(transport=httpx.MockTransport(respond))
    )
    monkeypatch.setenv("OPENROUTER_API_KEY", "offline")
    monkeypatch.setattr("openai.AsyncOpenAI", lambda **kwargs: client)
    async with model_context(
        ModelProfile(model="minimax/minimax-m3", tool_choice_required=False)
    ) as model:
        result = await Agent(model, output_type=SolutionOutput).run("fixture")
        assert result.output.answer == "done"


def test_carry_forward_preserves_allowances_and_reconciliation(tmp_path: Path) -> None:
    ledger = BudgetLedger(tmp_path / "source.json", 5)
    settled, _ = ledger.reserve_account(1, "test", "private-case", {"provider:key": 2})
    ledger.settle(settled, 0.5, "provider_reported", "settled-response")
    uncertain, _ = ledger.reserve_account(1, "test", "private-case", {"provider:key": 2})
    ledger.uncertain(uncertain)
    before = ledger.summary()
    target = tmp_path / "account.json"
    ledger.carry_forward(target)
    migrated = BudgetLedger(target, 5)
    assert migrated.summary() == before
    assert "private-case" not in target.read_text()
    with pytest.raises(BudgetExceeded):
        migrated.reserve_account(0.6, "test", "new-case", {"provider:key": 2})
    migrated.settle(uncertain, 0.2, "provider_reported", "reconciled-response")
    assert migrated.summary()["exposure_usd"] == pytest.approx(0.7)
    with pytest.raises(ValueError, match="must be new"):
        ledger.carry_forward(target)
    second = tmp_path / "second.json"
    migrated.carry_forward(second)
    assert BudgetLedger(second, 5).summary() == migrated.summary()
