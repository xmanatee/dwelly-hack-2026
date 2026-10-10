"""Analysis-only transport through the local Claude Code CLI subscription; no API key."""

from __future__ import annotations

import asyncio
import json
import shutil

from pydantic_ai.messages import (
    ModelMessage,
    ModelResponse,
    RetryPromptPart,
    ToolCallPart,
    UserPromptPart,
)
from pydantic_ai.models.function import AgentInfo, FunctionModel
from pydantic_ai.usage import RequestUsage

from dwelly_bot.contracts import ModelProfile, RunConfig

PREFIX = "claude-code/"


def transcript(messages: list[ModelMessage]) -> str:
    """Inputs, earlier structured outputs and validation feedback, in order."""
    lines: list[str] = []
    for message in messages:
        for part in message.parts:
            if isinstance(part, UserPromptPart):
                lines.append(str(part.content))
            elif isinstance(part, ToolCallPart):
                lines.append("Previous output:\n" + part.args_as_json_str())
            elif isinstance(part, RetryPromptPart):
                lines.append("Validation feedback:\n" + part.model_response())
    return "\n\n".join(lines)


def claude_code_profile(config: RunConfig) -> ModelProfile:
    """Subscription calls are unbilled; API-equivalent prices keep the local ledger a quota guard."""
    return ModelProfile(
        model=config.model,
        provider="anthropic",
        input_price_per_million=config.input_price_per_million or 3,
        output_price_per_million=config.output_price_per_million or 15,
        max_tokens=config.max_tokens,
    )


def claude_code_model(model: str) -> FunctionModel:
    executable = shutil.which("claude")
    if executable is None:
        raise ValueError(f"{model} requires the Claude Code CLI ('claude') on PATH")
    alias = model.removeprefix(PREFIX)

    async def respond(messages: list[ModelMessage], info: AgentInfo) -> ModelResponse:
        if len(info.output_tools) != 1 or info.function_tools:
            raise ValueError("Claude Code analysis supports exactly one structured output")
        [tool] = info.output_tools
        process = await asyncio.create_subprocess_exec(
            executable,
            "-p",
            "--output-format=json",
            "--model",
            alias,
            "--system-prompt",
            info.instructions or "",
            "--tools=",
            "--strict-mcp-config",
            "--no-session-persistence",
            "--json-schema",
            json.dumps(tool.parameters_json_schema),
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        try:
            stdout, stderr = await process.communicate(transcript(messages).encode())
        except BaseException:
            process.kill()
            raise
        try:
            result = json.loads(stdout)
        except json.JSONDecodeError as error:
            raise RuntimeError(f"Claude Code CLI failed: {stderr.decode()[-500:]}") from error
        if process.returncode or result.get("is_error") or "structured_output" not in result:
            raise RuntimeError(
                f"Claude Code CLI failed: {result.get('subtype')}: {str(result.get('result'))[:500]}"
            )
        usage = result.get("usage", {})
        return ModelResponse(
            parts=[ToolCallPart(tool.name, result["structured_output"])],
            usage=RequestUsage(
                input_tokens=usage.get("input_tokens", 0)
                + usage.get("cache_creation_input_tokens", 0)
                + usage.get("cache_read_input_tokens", 0),
                output_tokens=usage.get("output_tokens", 0),
            ),
            model_name=model,
            provider_response_id=result.get("session_id"),
            # The CLI reports list-price cost; a subscription is not billed per call.
            provider_details={
                "cost": result.get("total_cost_usd"),
                "billing": "claude_code_subscription_api_equivalent",
            },
        )

    return FunctionModel(respond, model_name=model)
