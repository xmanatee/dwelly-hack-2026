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
    conversation = Conversation(
        ElevenLabs(api_key=api_key),
        agent_id,
        requires_auth=bool(api_key),  # private agents need a signed URL from the API key
        audio_interface=audio,
        client_tools=tools,
        callback_agent_response=lambda text: print(f"Agent:  {text}", flush=True),
        callback_user_transcript=lambda text: print(f"Caller: {text}", flush=True),
        callback_end_session=ended.set,
    )
    calls.open(session_id)
    print(
        f"Session {session_id}: {'type messages, empty line ends' if args.text else 'speak now, Ctrl+C ends'}"
    )
    conversation.start_session()  # type: ignore[no-untyped-call]
    try:
        if args.text:
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
    args = parser.parse_args(argv)
    try:
        if args.output.exists():
            raise ValueError(f"Capture directory already exists: {args.output}")
        args.output.mkdir(parents=True)
        return ask(args) if args.command == "ask" else call(args)
    except (OSError, ValueError) as exc:
        parser.exit(2, f"Voice failed: {exc}\n")


if __name__ == "__main__":
    raise SystemExit(main())
