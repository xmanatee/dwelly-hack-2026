import json
from datetime import UTC, datetime
from pathlib import Path

import pytest

from dwelly_bot.channels.elevenlabs import ElevenLabsCallBridge
from dwelly_bot.channels.intake import Inbound
from dwelly_bot.channels.live_call import LiveCalls
from dwelly_bot.context.collector import ContextCollector
from dwelly_bot.context.sources import JsonSource
from dwelly_bot.demo_cli import FixturePlanner
from dwelly_bot.execution import MockExecutor
from dwelly_bot.execution.contracts import ExecutionResult
from dwelly_bot.filelock import lock_exclusive
from dwelly_bot.harness.production import ProductionPipeline
from dwelly_bot.planning import Plan
from dwelly_bot.voice_cli import main as voice_main

EXAMPLES = Path(__file__).parents[1] / "examples" / "voice"
PLAN = Plan.model_validate_json((EXAMPLES / "plan.json").read_text(encoding="utf-8"))


def bridge(
    tmp_path: Path, plan: Plan, calls: LiveCalls, session: str = "s1"
) -> ElevenLabsCallBridge:
    async def run(event: Inbound, output: Path, live: LiveCalls) -> ExecutionResult:
        return await ProductionPipeline(
            ContextCollector((JsonSource(EXAMPLES / "records.json"),)),
            FixturePlanner(plan),
            MockExecutor(live_calls=live),
        ).run(event, output)

    return ElevenLabsCallBridge(
        scope_id="voice-demo-transfer",
        caller="voice-demo-caller",
        session_id=session,
        output=tmp_path,
        run=run,
        calls=calls,
        clock=lambda: datetime(2026, 10, 10, 12, tzinfo=UTC),
    )


async def test_reply_is_spoken_in_the_open_call(tmp_path: Path) -> None:
    calls = LiveCalls()
    calls.open("s1")
    reply = json.loads(
        await bridge(tmp_path, PLAN, calls).ask(
            {"request": "Did my 350 pound transfer go?", "caller_name": "Jamie Rowe"}
        )
    )
    assert reply["status"] == "answered"
    assert reply["say"].startswith("Your 350 pounds to Kestrel Joinery shows as sent")
    assert reply["handoff"] == "human-support"
    assert reply["handoff_status"] == "simulated"
    assert reply["reference"] == "s1-001"
    capture = tmp_path / "s1-001"
    trigger = json.loads((capture / "trigger.json").read_text(encoding="utf-8"))
    assert trigger["reply_route"] == {"channel": "call", "session_id": "s1", "active": True}
    assert trigger["hints"]["name"] == "Jamie Rowe"
    context = (capture / "context.md").read_text(encoding="utf-8")
    assert "TRF-4417" in context and "LIVE CALL REPLY" in context
    receipts = json.loads((capture / "result.json").read_text(encoding="utf-8"))["receipts"]
    assert [(r["operation"], r["status"]) for r in receipts] == [
        ("handoff", "simulated"),
        ("speak_in_call", "sent"),
    ]
    assert calls.take("s1") == ()  # nothing left over for the next request


async def test_closed_call_gets_no_speech_and_no_callback(tmp_path: Path) -> None:
    calls = LiveCalls()  # session never opened, e.g. the caller hung up
    reply = json.loads(await bridge(tmp_path, PLAN, calls).ask({"request": "Status?"}))
    assert reply["status"] == "failed" and reply["say"] == ""
    assert not (tmp_path / "s1-001").exists()


async def test_calculated_value_reaches_the_caller(tmp_path: Path) -> None:
    plan = Plan.model_validate_json(
        (Path(__file__).parents[1] / "examples/production/calculation-plan.json").read_text(
            encoding="utf-8"
        )
    )
    calls = LiveCalls()
    calls.open("s1")
    reply = json.loads(await bridge(tmp_path, plan, calls).ask({"request": "Add 125.50 and 24.50"}))
    assert reply["say"] == "Total of the supplied amounts: 150.00."


async def test_missing_request_does_not_trigger_the_pipeline(tmp_path: Path) -> None:
    calls = LiveCalls()
    calls.open("s1")
    reply = json.loads(await bridge(tmp_path, PLAN, calls).ask({"request": "  "}))
    assert reply["status"] == "failed"
    assert not (tmp_path / "s1-001").exists()


async def test_pipeline_failure_is_reported_not_spoken(tmp_path: Path) -> None:
    async def broken(event: Inbound, output: Path, live: LiveCalls) -> ExecutionResult:
        live.say("s1", "half-finished speech")
        raise RuntimeError("source down")

    calls = LiveCalls()
    calls.open("s1")
    voice = bridge(tmp_path, PLAN, calls)
    voice.run = broken
    reply = json.loads(await voice.ask({"request": "Status?"}))
    assert reply["status"] == "failed" and reply["say"] == ""
    assert calls.take("s1") == ()


def test_offline_ask_command(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    code = voice_main(
        [
            "ask",
            "--scope",
            "voice-demo-transfer",
            "--records",
            str(EXAMPLES / "records.json"),
            "--plan",
            str(EXAMPLES / "plan.json"),
            "--output",
            str(tmp_path / "run"),
            "--request",
            "Has my transfer to Kestrel Joinery arrived?",
        ]
    )
    reply = json.loads(capsys.readouterr().out)
    assert code == 0 and reply["status"] == "answered" and reply["handoff"] == "human-support"


def test_lock_is_exclusive_across_handles(tmp_path: Path) -> None:
    path = tmp_path / "ledger.lock"
    with path.open("a+") as first, path.open("a+") as second:
        lock_exclusive(first)
        with pytest.raises(BlockingIOError):
            lock_exclusive(second, blocking=False)


async def test_failed_result_discards_partial_speech(tmp_path: Path) -> None:
    async def failed(event: Inbound, output: Path, live: LiveCalls) -> ExecutionResult:
        live.say("s1", "Do not deliver a partial success")
        return ExecutionResult(
            event_id=event.event_id, status="failed", disposition="failed", receipts=()
        )

    calls = LiveCalls()
    calls.open("s1")
    voice = bridge(tmp_path, PLAN, calls)
    voice.run = failed
    reply = json.loads(await voice.ask({"request": "Status?"}))
    assert reply["status"] == "failed" and not reply["say"] and not reply["handoff"]
    assert calls.take("s1") == ()


def test_voice_state_cannot_modify_source_database(tmp_path: Path) -> None:
    import sqlite3

    source = tmp_path / "source.sqlite"
    with sqlite3.connect(source) as db:
        db.execute("CREATE TABLE source_data (id TEXT)")
    before = source.read_bytes()
    with pytest.raises(SystemExit) as error:
        voice_main(
            [
                "ask",
                "--scope",
                "test",
                "--sqlite",
                str(source),
                "--state",
                str(source),
                "--request",
                "Status?",
                "--output",
                str(tmp_path / "output"),
            ]
        )
    assert error.value.code == 2
    assert source.read_bytes() == before
    assert not (tmp_path / "output").exists()
