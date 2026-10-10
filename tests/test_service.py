import asyncio
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import httpx
import pytest

pytest.importorskip("fastapi")

from dwelly_bot.channels.intake import CallInput, Inbound
from dwelly_bot.context.collector import ContextCollector
from dwelly_bot.execution import MockExecutor
from dwelly_bot.harness.production import ProductionPipeline
from dwelly_bot.planning import HumanReviewPlanner, Plan
from dwelly_bot.service.app import create_app
from dwelly_bot.service.backend import PipelineBackend
from dwelly_bot.service.store import SessionStore


def event() -> CallInput:
    return CallInput(
        event_id="original",
        scope_id="scope-a",
        caller="+440000000",
        received_at=datetime.now(UTC),
        text="Original issue",
        session_id="old",
    )


async def test_http_auth_replay_conflict_and_scope(tmp_path: Path) -> None:
    store = SessionStore(tmp_path / "state.sqlite")
    session, token = store.create(event())
    second, _ = store.create(event().model_copy(update={"scope_id": "other"}))
    observed: list[Inbound] = []

    async def backend(e: Inbound, s: str, r: str) -> dict[str, Any]:
        observed.append(e)
        return {"status": "complete", "execution": "mock"}

    app = create_app(store, backend)
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://test"
    ) as client:
        url = f"/sessions/{session}/turns"
        headers = {"Authorization": f"Bearer {token}"}
        body = {"request_id": "r1", "text": "Where is the payment?"}
        assert (await client.post(url, json=body)).status_code == 401
        assert (
            await client.post(f"/sessions/{second}/turns", json=body, headers=headers)
        ).status_code == 401
        assert (
            await client.post(url, json={**body, "scope_id": "other"}, headers=headers)
        ).status_code == 422
        assert (await client.post(url, json=body, headers=headers)).status_code == 200
        assert observed[0].scope_id == "scope-a" and isinstance(observed[0], CallInput)
        assert observed[0].session_id == session
        # New app/store instance simulates process restart, retaining the same result.
        restarted = create_app(SessionStore(store.path), backend)
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=restarted), base_url="http://test"
        ) as again:
            replay = await again.post(url, json=body, headers=headers)
            assert replay.headers["x-dwelly-replayed"] == "true" and len(observed) == 1
        assert (
            await client.post(url, json={**body, "text": "Changed"}, headers=headers)
        ).status_code == 409
        assert (await client.post(f"/sessions/{session}/close", headers=headers)).status_code == 200
        assert (
            await client.post(url, json={**body, "request_id": "r2"}, headers=headers)
        ).status_code == 410
    assert token not in store.path.read_bytes().decode(errors="ignore")


async def test_inflight_serialization_timeout_and_error_redaction(tmp_path: Path) -> None:
    store = SessionStore(tmp_path / "state.sqlite")
    session, token = store.create(event())
    started = asyncio.Event()

    async def backend(e: Inbound, s: str, r: str) -> dict[str, Any]:
        started.set()
        await asyncio.sleep(10)
        raise RuntimeError("private credential must not leak")

    app = create_app(store, backend, timeout=0.05)
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://test"
    ) as client:
        headers = {"Authorization": f"Bearer {token}"}
        url = f"/sessions/{session}/turns"
        first = asyncio.create_task(
            client.post(url, headers=headers, json={"request_id": "r1", "text": "help"})
        )
        await started.wait()
        assert (
            await client.post(url, headers=headers, json={"request_id": "r2", "text": "help"})
        ).status_code == 409
        result = await first
        assert result.status_code == 504 and "private credential" not in result.text
        assert (
            await client.post(url, headers=headers, json={"request_id": "r1", "text": "help"})
        ).status_code == 504


async def test_service_runs_real_offline_pipeline_and_keeps_history(tmp_path: Path) -> None:
    store = SessionStore(tmp_path / "sessions.sqlite")
    session, token = store.create(event())
    backend = PipelineBackend(store, (), tmp_path / "captures")
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=create_app(store, backend)), base_url="http://test"
    ) as client:
        for n, text in [(1, "I need help"), (2, "I mean the transfer from yesterday")]:
            reply = await client.post(
                f"/sessions/{session}/turns",
                headers={"Authorization": f"Bearer {token}"},
                json={"request_id": f"r{n}", "text": text},
            )
            assert reply.status_code == 200
            assert reply.json()["external_effects"] is False
        contexts = list((tmp_path / "captures").glob("*/context.md"))
        assert len(contexts) == 2
        assert any("Prior customer message" in p.read_text() for p in contexts)
        assert len(store.history(session)) == 2


async def test_disconnect_after_planning_prevents_execution(tmp_path: Path) -> None:
    active = True

    class ClosingPlanner:
        async def plan(self, context: str) -> Plan:
            nonlocal active
            active = False
            return await HumanReviewPlanner().plan(context)

    executor = MockExecutor()
    pipeline = ProductionPipeline(ContextCollector(()), ClosingPlanner(), executor)
    with pytest.raises(ValueError, match="closed before execution"):
        await pipeline.run(event(), tmp_path / "capture", is_active=lambda: active)
    assert not executor.effects
    assert (tmp_path / "capture/plan.json").is_file()
    assert (tmp_path / "capture/failure.json").is_file()


def test_expired_work_is_not_rerun_and_inactive_binding_rejected(tmp_path: Path) -> None:
    store = SessionStore(tmp_path / "state.sqlite")
    with pytest.raises(ValueError, match="inactive"):
        store.create(event().model_copy(update={"active": False}))
    session, _ = store.create(event())
    assert store.claim(session, "r1", "digest", "help", -1) is None
    replay = SessionStore(store.path).claim(session, "r1", "digest", "help", 10)
    assert replay is not None and replay[0] == 504
