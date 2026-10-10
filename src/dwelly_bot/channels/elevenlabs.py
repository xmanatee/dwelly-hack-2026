"""ElevenLabs voice agent → call trigger → pipeline → speech returned to the same call.

The voice agent calls one client tool, `ask_dwelly`. The SDK delivers that call over the
WebSocket our process opened, so no public endpoint is needed. This module has no SDK
dependency: `voice_cli` wires it to the ElevenLabs conversation.
"""

import asyncio
import logging
from collections.abc import Awaitable, Callable, Mapping
from datetime import UTC, datetime
from pathlib import Path
from typing import Literal

from dwelly_bot.channels.intake import CallInput, Contract, IdentityHints, Inbound
from dwelly_bot.channels.live_call import LiveCalls
from dwelly_bot.execution.contracts import ExecutionResult

TOOL_NAME = "ask_dwelly"
logger = logging.getLogger(__name__)

type CallRunner = Callable[[Inbound, Path, LiveCalls], Awaitable[ExecutionResult]]


class CallReply(Contract):
    """Tool result the voice agent reads; `say` is the only text meant for the caller."""

    status: Literal["answered", "no_answer", "failed"]
    say: str
    handoff: str | None = None
    handoff_status: Literal["simulated", "sent"] | None = None
    disposition: str | None = None
    reference: str


def _text(parameters: Mapping[str, object], key: str) -> str:
    value = parameters.get(key)
    return value.strip() if isinstance(value, str) else ""


class ElevenLabsCallBridge:
    """One live voice session. Scope and caller come from trusted local configuration."""

    def __init__(
        self,
        *,
        scope_id: str,
        caller: str,
        session_id: str,
        output: Path,
        run: CallRunner,
        calls: LiveCalls,
        clock: Callable[[], datetime] = lambda: datetime.now(UTC),
    ) -> None:
        self.scope_id, self.caller, self.session_id = scope_id, caller, session_id
        self.output, self.run, self.calls, self.clock = output, run, calls, clock
        self.turns = 0
        self._serial = asyncio.Lock()

    @property
    def busy(self) -> bool:
        """True while a request is running through the pipeline."""
        return self._serial.locked()

    async def ask(self, parameters: Mapping[str, object]) -> str:
        """Client-tool handler: returns a CallReply as JSON for the voice agent."""
        async with self._serial:  # one pipeline run at a time keeps speech per request
            self.turns += 1
            reference = f"{self.session_id}-{self.turns:03d}"
            request = _text(parameters, "request")
            if not self.calls.is_open(self.session_id):
                return CallReply(
                    status="failed", say="", reference=reference, disposition="Call is closed."
                ).model_dump_json()
            if not request or len(request) > 16000:
                return CallReply(
                    status="failed",
                    say="",
                    reference=reference,
                    disposition="Request must contain between 1 and 16000 characters.",
                ).model_dump_json()
            name, ref = _text(parameters, "caller_name"), _text(parameters, "reference")
            event = CallInput(
                event_id=reference,
                scope_id=self.scope_id,
                received_at=self.clock(),
                text=request,
                caller=self.caller,
                session_id=self.session_id,
                hints=IdentityHints(name=name or None, references=(ref,) if ref else ()),
            )
            self.calls.take(self.session_id)  # discard anything not produced by this request
            try:
                result = await self.run(event, self.output / reference, self.calls)
            except Exception:
                logger.exception("Pipeline failed for %s", reference)
                self.calls.take(self.session_id)
                return CallReply(
                    status="failed",
                    say="",
                    reference=reference,
                    disposition="The case system could not complete this request.",
                ).model_dump_json()
            spoken = self.calls.take(self.session_id)
            if result.status == "failed" or not self.calls.is_open(self.session_id):
                return CallReply(
                    status="failed",
                    say="",
                    reference=reference,
                    disposition="Execution failed or the call closed; no completion confirmed.",
                ).model_dump_json()
            handoffs = [
                r.parameters.get("queue", r.target)
                for r in result.receipts
                if r.operation == "handoff" and r.status in {"simulated", "sent"}
            ]
            return CallReply(
                status="answered" if spoken else "no_answer",
                say=" ".join(spoken),
                handoff=", ".join(handoffs) or None,
                handoff_status=(
                    "simulated"
                    if any(
                        r.operation == "handoff" and r.status == "simulated"
                        for r in result.receipts
                    )
                    else "sent"
                )
                if handoffs
                else None,
                disposition=result.disposition,
                reference=reference,
            ).model_dump_json()
