"""Credential pools with no credentials in configuration, receipts or exceptions."""

from __future__ import annotations

import os
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

from dotenv import dotenv_values
from pydantic_ai.models import Model
from pydantic_ai.models.wrapper import WrapperModel

from dwelly_bot.contracts import ModelProfile, RunConfig
from dwelly_bot.paths import ROOT, default_ledger


def profile_for(config: RunConfig) -> ModelProfile:
    return ModelProfile.model_validate(config.model_dump(include=set(ModelProfile.model_fields)))


def ledger_path(config: RunConfig) -> Path:
    return (ROOT / config.budget_file).resolve() if config.budget_file else default_ledger()


def credentials(profile: ModelProfile) -> dict[str, str]:
    names = profile.key_envs or [profile.provider.upper() + "_API_KEY"]
    local = dotenv_values(ROOT / ".env")
    found = {name: os.environ.get(name) or local.get(name) for name in names}
    if any(not value for value in found.values()):
        raise ValueError(
            "Missing credential environment variables: "
            + ", ".join(n for n, v in found.items() if not v)
        )
    return {name: str(value) for name, value in found.items()}


class ModelPool(WrapperModel):
    """BudgetedModel selects a credential atomically with its spending reservation."""

    def __init__(self, models: dict[str, Model], clients: list[Any], profile: ModelProfile) -> None:
        super().__init__(next(iter(models.values())))
        self.models, self.clients, self.connection_profile = models, clients, profile

    async def close(self) -> None:
        for client in self.clients:
            await client.close()


@asynccontextmanager
async def model_context(profile: ModelProfile) -> AsyncIterator[ModelPool]:
    pool = model_pool(profile)
    try:
        yield pool
    finally:
        await pool.close()


def model_pool(profile: ModelProfile) -> ModelPool:
    models: dict[str, Model] = {}
    clients: list[Any] = []
    for name, key in credentials(profile).items():
        if profile.provider == "anthropic":
            from anthropic import AsyncAnthropic
            from pydantic_ai.models.anthropic import AnthropicModel
            from pydantic_ai.providers.anthropic import AnthropicProvider

            client: Any = AsyncAnthropic(api_key=key, max_retries=0)
            model: Model = AnthropicModel(
                profile.model, provider=AnthropicProvider(anthropic_client=client)
            )
        else:
            from openai import AsyncOpenAI

            client = AsyncOpenAI(
                api_key=key,
                max_retries=0,
                base_url="https://openrouter.ai/api/v1"
                if profile.provider == "openrouter"
                else None,
            )
            if profile.provider == "openrouter":
                from pydantic_ai.models.openrouter import OpenRouterModel
                from pydantic_ai.profiles.openai import OpenAIModelProfile
                from pydantic_ai.providers.openrouter import OpenRouterProvider

                model = OpenRouterModel(
                    profile.model,
                    provider=OpenRouterProvider(openai_client=client),
                    profile=OpenAIModelProfile(
                        supports_forced_tool_choice=profile.tool_choice_required
                    ),
                )
            else:
                from pydantic_ai.models.openai import OpenAIResponsesModel
                from pydantic_ai.providers.openai import OpenAIProvider

                model = OpenAIResponsesModel(
                    profile.model, provider=OpenAIProvider(openai_client=client)
                )
        clients.append(client)
        models[f"{profile.provider}:{name}"] = model
    return ModelPool(models, clients, profile)
