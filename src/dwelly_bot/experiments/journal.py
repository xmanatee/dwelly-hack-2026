"""Local write-ahead tool journal. No remote logging or model instrumentation."""

# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

import asyncio
import inspect
import json
import os
import time
import traceback
import uuid
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from dwelly_bot.budget import BudgetExceeded
from dwelly_bot.contracts import StateReader, Subject
from dwelly_bot.storage import fingerprint, json_bytes, save_json


def timestamp() -> str:
    return datetime.now(UTC).isoformat()


class Journal:
    def __init__(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        self.file = path.open("x")
        self.events: list[dict[str, Any]] = []

    def append(self, event: dict[str, Any]) -> None:
        self.file.write(json.dumps(event, ensure_ascii=False, allow_nan=False) + "\n")
        self.file.flush()
        os.fsync(self.file.fileno())

    @contextmanager
    def record(
        self,
        tool: str,
        arguments: dict[str, Any],
        *,
        title: str | None = None,
        intent: str | None = None,
        kind: str = "tool",
        read_only: bool | None = None,
        role: str | None = None,
    ) -> Iterator[dict[str, Any]]:
        """One durable lifecycle for tool calls."""
        event: dict[str, Any] = {
            "id": "T-" + uuid.uuid4().hex,
            "tool": tool,
            "title": title,
            "intent": intent,
            "kind": kind,
            "role": role,
            "read_only": read_only,
            "arguments": json.loads(json_bytes(arguments)),
            "started_at": timestamp(),
            "status": "started",
        }
        self.append(dict(event))  # Persist before invoking a tool that may mutate state.
        self.events.append(event)
        start = time.monotonic()
        try:
            yield event
        except asyncio.CancelledError as exc:
            event.update(
                status="unconfirmed",
                error={
                    "type": type(exc).__name__,
                    "message": "No acknowledgement before cancellation",
                },
            )
            raise
        except BaseException as exc:
            event.update(
                status="error",
                error={
                    "type": type(exc).__name__,
                    "message": str(exc),
                    "traceback": "".join(traceback.format_exception(exc)),
                },
            )
            raise
        finally:
            event.update(
                ended_at=timestamp(), elapsed_ms=round((time.monotonic() - start) * 1000, 2)
            )
            self.append(dict(event))

    @staticmethod
    def returned(event: dict[str, Any], value: Any) -> Any:
        result = json.loads(json_bytes(value))
        event.update(result=result, status="returned")
        return result

    async def call(
        self, tool: str, arguments: dict[str, Any], invoke: Callable[..., Any], **metadata: Any
    ) -> Any:
        with self.record(tool, arguments, **metadata) as event:
            result = invoke(**arguments)
            if inspect.isawaitable(result):
                result = await result
            return self.returned(event, result)

    def close(self) -> None:
        self.file.close()


def recover_events(path: Path) -> list[dict[str, Any]]:
    """Recover started calls as unconfirmed; this function never retries them."""
    events: dict[str, dict[str, Any]] = {}
    for line in path.read_text().splitlines():
        if not line.strip():
            continue
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            raise ValueError(
                "Truncated journal record; inspect rather than inventing a result"
            ) from None
        events[event["id"]] = event
    return [
        dict(e, status="unconfirmed") if e["status"] == "started" else e for e in events.values()
    ]


async def capture_case(
    case: dict[str, Any],
    directory: Path,
    subject: Subject,
    read_state: StateReader | None = None,
    timeout: float = 90,
) -> dict[str, Any]:
    """Subject returns JSON answer/rationale/disposition; snapshot callback is read-only."""
    output = {
        "id": case["id"],
        "title": case.get("title", case["id"]),
        "input": case["input"],
        "input_hash": fingerprint(case["input"]),
        "execution_status": "running",
        "tool_events": [],
        "state_snapshots": {},
        "verifier": {"status": "not_run"},
        "judge": [],
    }
    for key in ["evaluation_contract", "sources", "input_scope"]:
        if key in case:
            output[key] = case[key]  # Kept out of subject inputs; contracts are grading metadata.
    directory.mkdir(parents=True, exist_ok=False)
    save_json(
        directory / "input.json",
        {
            key: value
            for key, value in output.items()
            if key
            in [
                "id",
                "title",
                "input",
                "input_hash",
                "evaluation_contract",
                "sources",
                "input_scope",
            ]
        },
    )
    journal = Journal(directory / "tools.jsonl")
    started = time.monotonic()

    async def snapshot(phase: str) -> None:
        if not read_state:
            return
        try:
            value = read_state()
            if inspect.isawaitable(value):
                value = await asyncio.wait_for(value, timeout=10)
            json.dumps(value, allow_nan=False)
            output["state_snapshots"][phase] = value
            digest = fingerprint(value)
            output["initial_state_hash" if phase == "before" else "final_state_hash"] = digest
        except Exception as exc:
            output.setdefault("state_capture_errors", {})[phase] = str(exc)

    try:
        await snapshot("before")
        result = await asyncio.wait_for(subject(case["input"], journal), timeout=timeout)
        for key in [
            "answer",
            "public_rationale",
            "agent_disposition",
            "usage",
        ]:
            if key in result:
                output[key] = result[key]
        output["execution_status"] = "completed"
    except Exception as exc:
        output.update(
            execution_status="error",
            agent_disposition="escalated",
            answer="This case requires human review because processing could not be completed.",
            public_rationale="A technical failure prevented completion; no resolution is confirmed.",
            error=f"{type(exc).__name__}: {exc}",
            error_traceback="".join(traceback.format_exception(exc)),
        )
        if isinstance(exc, (BudgetExceeded, TimeoutError)):
            output["stop_reason"] = "budget" if isinstance(exc, BudgetExceeded) else "timeout"
            for key in ("answer", "public_rationale", "agent_disposition"):
                output.pop(key, None)
    except asyncio.CancelledError:
        output.update(
            execution_status="cancelled", stop_reason="cancelled", error="Caller cancelled the case"
        )
        raise
    finally:
        await snapshot("after")
        output["tool_events"] = journal.events
        output["metrics"] = {
            "latency_ms": round((time.monotonic() - started) * 1000, 2),
            "tool_calls": len(journal.events),
            "cost_usd": None,
        }
        journal.close()
        save_json(directory / "execution.json", output)
    return output
