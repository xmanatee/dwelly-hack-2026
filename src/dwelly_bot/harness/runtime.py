"""Bounded SDK calls, typed tools and local-only execution traces."""

from __future__ import annotations

import asyncio
import functools
import hashlib
import inspect
import json
from collections.abc import Callable
from contextlib import nullcontext
from contextvars import ContextVar
from typing import Any, TypeVar, get_type_hints

from pydantic import BaseModel
from pydantic_ai import (
    Agent,
    AgentRunResult,
    FunctionToolset,
    InstructionPart,
    ModelMessagesTypeAdapter,
    ToolOutput,
    capture_run_messages,
)
from pydantic_ai.exceptions import ModelRetry
from pydantic_ai.messages import ModelMessage
from pydantic_ai.settings import ModelSettings
from pydantic_ai.tools import Tool
from pydantic_ai.toolsets import AbstractToolset
from pydantic_ai.usage import RunUsage, UsageLimits

from dwelly_bot import prompts
from dwelly_bot.context.skills import SkillLibrary
from dwelly_bot.contracts import Modules, RunConfig
from dwelly_bot.experiments.journal import Journal
from dwelly_bot.storage import json_bytes

OutputT = TypeVar("OutputT", bound=BaseModel)


class StatefulToolResultTooLarge(RuntimeError):
    """An action returned; delivery failed and repeating it would risk duplicate effects."""


class CaseRuntime:
    def __init__(
        self,
        model: Any,
        config: RunConfig,
        journal: Journal,
        *,
        planner_model: Any = None,
    ) -> None:
        self.model = model
        self.planner_model = planner_model
        self.config = config
        self.journal = journal
        self.usage = RunUsage()
        self.role_records: list[dict[str, Any]] = []
        self.policy_gate: Any = None
        self._role: ContextVar[str] = ContextVar("case_role", default="subject")

    def agent(
        self,
        *,
        output_type: type[OutputT],
        output_name: str,
        tools: list[Tool[Any]] | None = None,
        instructions: str | list[InstructionPart],
        toolsets: list[AbstractToolset[Any] | None] | None = None,
        output_description: str | None = None,
        role: str = "subject",
    ) -> Agent[Any, OutputT]:
        """Configure the acting model and its role-specific tools."""
        model = self.planner_model if role == "planner" and self.planner_model else self.model
        if model is None:
            raise ValueError(f"{role.capitalize()} role requires an explicit {role} model")
        if role == "subject" and self.config.skills and self.config.skill_mode == "on_demand":
            library = SkillLibrary(self.config.skills)
            toolsets = [
                *(toolsets or []),
                self.toolset(
                    "skills", {"list_skills": library.list_skills, "read_skill": library.read_skill}
                ),
            ]
        agent: Agent[Any, OutputT] = Agent(
            model=model,
            output_type=ToolOutput(
                output_type, name=output_name, description=output_description, strict=False
            ),
            tools=[
                t
                for t in (tools or [])
                if role != "subject" or t.name not in self.config.disabled_tools
            ],
            toolsets=[
                group.filtered(lambda _ctx, tool: tool.name not in self.config.disabled_tools)
                if role == "subject"
                else group
                for group in (toolsets or [])
                if group is not None
            ],
            instructions=instructions,
            retries=self.config.retries,
        )
        agent.instrument = False
        return agent

    def instructions(self, domain: str, *policies: str) -> list[InstructionPart]:
        return prompts.instructions(domain, self.config, *policies)

    def toolset(
        self,
        name: str,
        bindings: dict[str, Callable[..., Any]],
        *,
        module: str | None = None,
        read_only: bool = True,
    ) -> FunctionToolset[Any] | None:
        """Bind a named SDK toolset; all calls retain the shared guard/journal boundary."""
        if module is not None:
            if module not in Modules.model_fields:
                raise ValueError(f"Unknown tool module: {module}")
            if not getattr(self.config.modules, module):
                return None
        return FunctionToolset(
            [
                self.tool(key, function.__doc__ or key, function, read_only=read_only)
                for key, function in bindings.items()
            ],
            id=name,
        )

    def tool(
        self,
        name: str,
        description: str,
        function: Callable[..., Any],
        schema: dict[str, Any] | None = None,
        *,
        read_only: bool = False,
        manages_read_timeout: bool = False,
    ) -> Tool[Any]:
        signature = inspect.signature(function)

        @functools.wraps(function)
        async def invoke(*args: Any, **kwargs: Any) -> Any:
            arguments = (
                dict(signature.bind(*args, **kwargs).arguments) if schema is None else kwargs
            )

            async def actual(**_: Any) -> Any:
                if self.policy_gate:
                    self.policy_gate.guard(name, read_only)

                # Stateful synchronous actions remain inline; cancellation cannot leave
                # an unobserved mutation running in a worker thread.
                async with (
                    asyncio.timeout(self.config.tool_timeout_seconds)
                    if read_only and not manages_read_timeout
                    else nullcontext()
                ):
                    if read_only and not inspect.iscoroutinefunction(function):
                        value = await asyncio.to_thread(function, *args, **kwargs)
                    else:
                        value = function(*args, **kwargs)
                    if inspect.isawaitable(value):
                        value = await value
                encoded = json_bytes(value)
                if len(encoded) > self.config.max_tool_result_bytes:
                    if not read_only:
                        receipt = {
                            "response_bytes": len(encoded),
                            "response_sha256": hashlib.sha256(encoded).hexdigest(),
                        }
                        raise StatefulToolResultTooLarge(
                            "Stateful tool returned, but its response exceeds the byte limit. "
                            "Execution stops without retry; inspect the saved state and receipt: "
                            + json.dumps(receipt, sort_keys=True)
                        )
                    raise ModelRetry(
                        "Tool result exceeds the configured byte limit; use filters, pagination or aggregation."
                    )
                return value

            try:
                return await self.journal.call(
                    name,
                    arguments,
                    actual,
                    title=f"{self._role.get()}: {(description.splitlines() or [name])[0][:140]}",
                    kind=f"{self._role.get()}_tool",
                    role=self._role.get(),
                    read_only=read_only,
                )
            except OSError as error:
                if not read_only:
                    raise
                raise ModelRetry(
                    f"Read failed ({type(error).__name__}); retry or use another evidence source."
                ) from error

        invoke.__annotations__ = get_type_hints(function)

        if schema is not None:
            return Tool.from_schema(
                invoke, name=name, description=description, json_schema=schema, sequential=True
            )
        return Tool(invoke, name=name, description=description, takes_ctx=False, sequential=True)

    async def ask(
        self,
        agent: Agent[Any, Any],
        prompt: str | dict[str, Any],
        message_history: list[ModelMessage] | None = None,
        role: str = "subject",
    ) -> AgentRunResult[Any]:
        user_prompt = json.dumps(prompt, ensure_ascii=False) if isinstance(prompt, dict) else prompt
        role_token = self._role.set(role)
        agent.instrument = False
        with capture_run_messages() as messages:
            try:
                limits = UsageLimits(
                    request_limit=self.config.max_requests,
                    tool_calls_limit=self.config.max_tool_calls,
                    total_tokens_limit=self.config.max_total_tokens,
                    per_request_input_tokens_limit=self.config.max_input_tokens,
                )
                settings: ModelSettings = {
                    "max_tokens": self.config.max_tokens,
                    "timeout": self.config.request_timeout_seconds,
                }
                result = await agent.run(
                    user_prompt,
                    message_history=message_history,
                    usage=self.usage,
                    usage_limits=limits,
                    model_settings=settings,
                )
            finally:
                dumped = json.loads(ModelMessagesTypeAdapter.dump_json(messages))
                self.role_records.append({"role": role, "messages": dumped})
                self._role.reset(role_token)
        return result
