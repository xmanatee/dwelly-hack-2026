"""Explicit paid judging uses the same credential pools and persistent spending cap."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

from dwelly_bot.budget import BudgetLedger
from dwelly_bot.configuration import read_config as read_config
from dwelly_bot.contracts import RunConfig
from dwelly_bot.evaluation.judge import LlmJudge
from dwelly_bot.providers import ledger_path, model_context, profile_for


@asynccontextmanager
async def judge_context(
    path: Path, rubric: dict[str, Any]
) -> AsyncIterator[tuple[LlmJudge, RunConfig]]:
    config = read_config(path)
    async with model_context(profile_for(config)) as pool:
        yield (
            LlmJudge(
                pool,
                rubric,
                timeout=config.request_timeout_seconds,
                settings={"max_tokens": config.max_tokens},
                ledger=BudgetLedger(ledger_path(config), config.total_budget_usd),
                profile=profile_for(config),
            ),
            config,
        )
