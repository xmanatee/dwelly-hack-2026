"""Voice channel: an ElevenLabs agent triggers the call pipeline and speaks its reply.

`ask` runs one request through the same bridge without ElevenLabs (offline check).
`call` opens a live ElevenLabs conversation (microphone, or `--text` for a typed session).
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import threading
import time
import uuid
from collections.abc import Sequence
from pathlib import Path

from dotenv import dotenv_values

from dwelly_bot.channels.elevenlabs import TOOL_NAME, ElevenLabsCallBridge
from dwelly_bot.channels.intake import Inbound
from dwelly_bot.channels.live_call import LiveCalls
from dwelly_bot.context.collector import ContextSource
from dwelly_bot.context.sources import JsonSource, SQLiteSource
from dwelly_bot.demo_cli import FixturePlanner
from dwelly_bot.execution.contracts import ExecutionResult
from dwelly_bot.harness.local import run_local_pipeline
from dwelly_bot.paths import ROOT
from dwelly_bot.planning import HumanReviewPlanner, Plan, Planner
from dwelly_bot.storage import save_json


def setting(name: str) -> str | None:
    """Environment first, then the ignored local .env; values are never printed."""
    return os.environ.get(name) or dotenv_values(ROOT / ".env").get(name) or None


def build_bridge(
    args: argparse.Namespace, calls: LiveCalls, session_id: str
) -> ElevenLabsCallBridge:
    sources: list[ContextSource] = []
    if args.records:
        sources.append(JsonSource(args.records))
    if args.sqlite:
        sources.append(SQLiteSource(args.sqlite, table=args.table))
    planner: Planner = (
        FixturePlanner(Plan.model_validate_json(args.plan.read_text(encoding="utf-8")))
        if args.plan
        else HumanReviewPlanner()
    )

    async def run(event: Inbound, output: Path, live: LiveCalls) -> ExecutionResult:
        return await run_local_pipeline(
            event,
            tuple(sources),
            planner,
            output,
            state=args.state,
            context_config=args.context_config,
            live_calls=live,
        )

    return ElevenLabsCallBridge(
        scope_id=args.scope,
        caller=args.caller,
        session_id=session_id,
        output=args.output,
        run=run,
        calls=calls,
    )


def ask(args: argparse.Namespace) -> int:
    calls, session_id = LiveCalls(), f"voice-{uuid.uuid4().hex[:12]}"
    calls.open(session_id)
    bridge = build_bridge(args, calls, session_id)
    parameters = {"request": args.request, "caller_name": args.caller_name or "", "reference": ""}
    reply = asyncio.run(bridge.ask(parameters))
    print(json.dumps(json.loads(reply), indent=2, ensure_ascii=False))
    return 0 if json.loads(reply)["status"] != "failed" else 1


def call(args: argparse.Namespace) -> int:
    try:
        from elevenlabs.client import ElevenLabs
        from elevenlabs.conversational_ai.conversation import ClientTools, Conversation
        from elevenlabs.core.api_error import ApiError
    except ImportError:
        raise ValueError("Install the voice extra first: uv sync --extra voice") from None
    agent_id = args.agent_id or setting("ELEVENLABS_AGENT_ID")
    if not agent_id:
        raise ValueError("Set ELEVENLABS_AGENT_ID in .env or pass --agent-id")
    api_key = setting("ELEVENLABS_API_KEY")

    calls, session_id = LiveCalls(), f"voice-{uuid.uuid4().hex[:12]}"
    bridge = build_bridge(args, calls, session_id)
    tools = ClientTools()
    tools.register(TOOL_NAME, bridge.ask, is_async=True)
    audio = None
    if not args.text:
        from elevenlabs.conversational_ai.default_audio_interface import DefaultAudioInterface

        audio = DefaultAudioInterface()  # type: ignore[no-untyped-call]
    ended = threading.Event()
    replies: list[float] = []  # arrival times of agent turns, for scripted sessions

    def agent_said(text: str) -> None:
        replies.append(time.monotonic())
        print(f"Agent:  {text}", flush=True)

    def wait_for_agent(after: int, quiet: float = 6, limit: float = 120) -> None:
        """Wait for a new agent turn, then until it stays quiet (tool runs included)."""
        deadline = time.monotonic() + limit
        while time.monotonic() < deadline and not ended.is_set():
            idle = len(replies) > after and time.monotonic() - replies[-1] >= quiet
            if idle and not bridge.busy:
                return
            time.sleep(0.2)

    conversation = Conversation(
        ElevenLabs(api_key=api_key),
        agent_id,
        requires_auth=bool(api_key),  # private agents need a signed URL from the API key
        audio_interface=audio,
        client_tools=tools,
        callback_agent_response=agent_said,
        callback_user_transcript=lambda text: print(f"Caller: {text}", flush=True),
        callback_end_session=ended.set,
    )
    calls.open(session_id)
    mode = (
        "scripted caller"
        if args.say
        else "type messages, empty line ends"
        if args.text
        else "speak now, Ctrl+C ends"
    )
    print(f"Session {session_id}: {mode}")
    try:
        conversation.start_session()  # type: ignore[no-untyped-call]
    except ApiError as exc:
        calls.close(session_id)
        detail = exc.body.get("detail", exc.body) if isinstance(exc.body, dict) else exc.body
        message = detail.get("message", detail) if isinstance(detail, dict) else detail
        raise ValueError(f"ElevenLabs refused the session ({exc.status_code}): {message}") from None
    try:
        if args.say:
            wait_for_agent(0)
            for line in args.say:
                print(f"Caller: {line}", flush=True)
                seen = len(replies)
                conversation.send_user_message(line)
                wait_for_agent(seen)
        elif args.text:
            while not ended.is_set():
                line = input()
                if not line.strip():
                    break
                conversation.send_user_message(line)
        else:
            while not ended.wait(0.2):
                pass
    except (KeyboardInterrupt, EOFError):
        pass
    finally:
        calls.close(session_id)
        if not ended.is_set():
            conversation.end_session()  # type: ignore[no-untyped-call]
    conversation_id = conversation.wait_for_session_end()
    save_json(
        args.output / "session.json",
        {
            "session_id": session_id,
            "elevenlabs_conversation_id": conversation_id,
            "agent_id": agent_id,
            "scope_id": args.scope,
            "requests": bridge.turns,
        },
    )
    print(f"Session ended. Captures: {args.output}")
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    shared = argparse.ArgumentParser(add_help=False)
    shared.add_argument("--scope", required=True, help="Trusted case scope for this caller")
    shared.add_argument(
        "--caller", default="voice-demo-caller", help="Caller ID for the reply route"
    )
    shared.add_argument("--records", type=Path, help="Normalized JSON context records")
    shared.add_argument("--sqlite", type=Path, help="Read-only normalized database")
    shared.add_argument("--table", default="context_records")
    shared.add_argument(
        "--plan", type=Path, help="Saved Plan JSON; omitted means human-review stub"
    )
    shared.add_argument("--context-config", type=Path, help="Explicit paid context-agent RunConfig")
    shared.add_argument("--state", type=Path, help="Separate SQLite file for durable mock receipts")
    shared.add_argument("--output", required=True, type=Path, help="New capture directory")
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    one = commands.add_parser(
        "ask", parents=[shared], help="One request through the bridge, no ElevenLabs"
    )
    one.add_argument("--request", required=True)
    one.add_argument("--caller-name")
    live = commands.add_parser("call", parents=[shared], help="Live ElevenLabs conversation")
    live.add_argument("--agent-id", help="Defaults to ELEVENLABS_AGENT_ID")
    live.add_argument(
        "--text", action="store_true", help="Typed conversation instead of microphone"
    )
    live.add_argument(
        "--say",
        action="append",
        help="Scripted caller turn for a text session (repeatable); ends after the last reply",
    )
    args = parser.parse_args(argv)
    if getattr(args, "say", None):
        args.text = True
    try:
        if args.output.exists():
            raise ValueError(f"Capture directory already exists: {args.output}")
        args.output.mkdir(parents=True)
        return ask(args) if args.command == "ask" else call(args)
    except (OSError, ValueError) as exc:
        parser.exit(2, f"Voice failed: {exc}\n")


if __name__ == "__main__":
    raise SystemExit(main())
