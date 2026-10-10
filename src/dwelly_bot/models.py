"""Budgeted provider transport shared by agent, judge and analytics roles."""

from __future__ import annotations

import asyncio
import json
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from dataclasses import asdict
from decimal import Decimal
from typing import Any

from pydantic_ai import ModelMessagesTypeAdapter, RunContext
from pydantic_ai.messages import ModelMessage, ModelResponse
from pydantic_ai.models import ModelRequestParameters, StreamedResponse
from pydantic_ai.models.wrapper import WrapperModel
from pydantic_ai.settings import ModelSettings

from dwelly_bot.budget import BudgetLedger
from dwelly_bot.contracts import ModelProfile
from dwelly_bot.resources import text
from dwelly_bot.storage import json_bytes


class BudgetedModel(WrapperModel):
    """No SDK transport retries; every response or uncertain request is charged locally."""

    def __init__(
        self,
        wrapped: Any,
        ledger: BudgetLedger,
        case_id: str,
        request_timeout: float = 60,
        *,
        supports_reasoning: bool | None = None,
        profile: ModelProfile | None = None,
    ) -> None:
        super().__init__(wrapped)
        self.ledger = ledger
        self.case_id = case_id
        self.request_timeout = request_timeout
        known = json.loads(text("model-capabilities.json"))["reasoning"]
        self.supports_reasoning = (
            known.get(wrapped.model_name, False)
            if supports_reasoning is None
            else supports_reasoning
        )
        self.billing_profile = profile or ModelProfile(model=wrapped.model_name)
        self.calls: list[dict[str, Any]] = []

    def scoped(self, case_id: str) -> BudgetedModel:
        """Reuse transport/accounting settings while keeping this operation's call receipts separate."""
        return BudgetedModel(
            self.wrapped,
            self.ledger,
            case_id,
            self.request_timeout,
            supports_reasoning=self.supports_reasoning,
            profile=self.billing_profile,
        )

    async def request(
        self,
        messages: list[ModelMessage],
        model_settings: ModelSettings | None,
        model_request_parameters: ModelRequestParameters,
    ) -> ModelResponse:
        settings: Any = dict(model_settings or {})
        profile = self.billing_profile
        input_rate = profile.input_price_per_million or 1
        output_rate = profile.output_price_per_million or 6
        if profile.provider == "openrouter":
            settings["openrouter_usage"] = {"include": True}
            settings["openrouter_provider"] = {
                "sort": profile.provider_sort,
                "require_parameters": True,
                "max_price": {"prompt": input_rate, "completion": output_rate},
            }
            if self.supports_reasoning or profile.reasoning_effort or profile.reasoning_enabled:
                settings["openrouter_reasoning"] = (
                    {"effort": profile.reasoning_effort}
                    if profile.reasoning_effort
                    else {"enabled": profile.reasoning_enabled}
                )
            if profile.provider_only:
                settings["openrouter_provider"]["only"] = profile.provider_only
        elif profile.reasoning_effort:
            if profile.provider == "anthropic":
                settings["anthropic_thinking"] = {"type": "adaptive"}
                settings["anthropic_effort"] = profile.reasoning_effort
            else:
                settings["openai_reasoning_effort"] = profile.reasoning_effort
        if profile.anthropic_cache:
            settings["anthropic_cache"] = "5m"
        max_tokens = settings.get("max_tokens", 2048)
        # UTF-8 bytes conservatively estimate input token exposure. Direct providers
        # use configured ceilings; OpenRouter also enforces these in provider selection.
        size = len(ModelMessagesTypeAdapter.dump_json(messages))
        size += sum(
            len(part.content.encode())
            for part in (model_request_parameters.instruction_parts or [])
        )
        size += len(
            json.dumps([asdict(t) for t in model_request_parameters.function_tools]).encode()
        )
        size += len(json.dumps([asdict(t) for t in model_request_parameters.output_tools]).encode())
        reservation = (size + 4096) * input_rate * (
            1.25 if profile.anthropic_cache else 1
        ) / 1_000_000 + max_tokens * output_rate / 1_000_000
        pool = getattr(self.wrapped, "models", None)
        accounts = {name: profile.account_budget_usd for name in pool} if pool else None
        token, account = self.ledger.reserve_account(
            reservation, self.model_name, self.case_id, accounts
        )
        transport = pool[account] if pool else self.wrapped
        try:
            async with asyncio.timeout(self.request_timeout):
                response = await transport.request(messages, settings, model_request_parameters)
            # OpenRouter billing lives in provider_details; SDK usage.cost may instead
            # be an independently estimated catalog price populated after this wrapper.
            reported = (response.provider_details or {}).get("cost")
            basis = (
                "provider_reported" if reported is not None else "provider_price_cap_upper_bound"
            )
            if reported is not None:
                cost = Decimal(str(reported))
            elif response.usage.input_tokens or response.usage.output_tokens:
                billed_input = Decimal(response.usage.input_tokens)
                if profile.anthropic_cache:
                    # Five-minute writes cost 1.25x; 0.1x reads conservatively bound newer discounts.
                    billed_input += Decimal(response.usage.cache_write_tokens) * Decimal("0.25")
                    billed_input -= Decimal(response.usage.cache_read_tokens) * Decimal("0.9")
                cost = billed_input * Decimal(str(input_rate)) / 1_000_000
                cost += (
                    Decimal(response.usage.output_tokens) * Decimal(str(output_rate)) / 1_000_000
                )
                if profile.provider != "openrouter":
                    basis = "configured_token_price_upper_bound"
            else:
                cost = Decimal(str(reservation))
                basis = "unconfirmed_usage_upper_bound"
            record = {
                "status": "settled",
                "account": account,
                "response_id": response.provider_response_id,
                "cost_usd": float(cost),
                "cost_basis": basis,
                "sdk_cost_estimate": str(response.usage.cost)
                if response.usage.cost is not None
                else None,
                "usage": json.loads(json_bytes(response.usage)),
            }
            self.ledger.settle(token, float(cost), basis, response.provider_response_id)
            self.calls.append(record)
            return response
        except BaseException as error:
            self.ledger.uncertain(token)
            self.calls.append(
                {
                    "status": "uncertain",
                    "account": account,
                    "cost_usd": None,
                    "reserved_usd": reservation,
                    "cost_basis": "unconfirmed_request",
                }
            )
            if isinstance(error, (asyncio.CancelledError, TimeoutError)):
                raise
            if (
                pool
                and account
                and (
                    getattr(error, "status_code", None) in {401, 403, 429}
                    or type(error).__name__
                    in {"AuthenticationError", "PermissionDeniedError", "RateLimitError"}
                )
            ):
                self.ledger.cooldown(account)
                # Rejected credentials can be rotated safely. Other failures retain
                # an uncertain receipt without a hidden retry.
                if len(pool) > 1:
                    return await self.request(messages, model_settings, model_request_parameters)
            if pool:
                raise RuntimeError(
                    f"{profile.provider} request failed ({type(error).__name__}, HTTP {getattr(error, 'status_code', 'unknown')}); reservation retained"
                ) from None
            raise

    @asynccontextmanager
    async def request_stream(
        self,
        messages: list[ModelMessage],
        model_settings: ModelSettings | None,
        model_request_parameters: ModelRequestParameters,
        run_context: RunContext[Any] | None = None,
    ) -> AsyncGenerator[StreamedResponse]:
        raise RuntimeError(
            "Streaming is disabled: all paid requests must use the budgeted request path"
        )
        yield  # pragma: no cover
