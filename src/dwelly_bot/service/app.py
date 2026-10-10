"""FastAPI transport: authenticated text turns for ElevenLabs, email or ticket adapters."""

import asyncio
import math
from collections.abc import Awaitable, Callable
from datetime import UTC, datetime
from typing import Annotated, Any

from fastapi import FastAPI, Header, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, Field, ValidationError

from dwelly_bot.channels.intake import Inbound, inbound_adapter
from dwelly_bot.service.store import Conflict, SessionStore
from dwelly_bot.storage import fingerprint


class Turn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    request_id: str = Field(min_length=1, max_length=100, pattern=r"^[A-Za-z0-9_-]+$")
    text: str = Field(min_length=1, max_length=16000, pattern=r"\S")


type Backend = Callable[[Inbound, str, str], Awaitable[dict[str, Any]]]


def create_app(store: SessionStore, backend: Backend, *, timeout: float = 45) -> FastAPI:
    if not math.isfinite(timeout) or timeout <= 0:
        raise ValueError("Request timeout must be finite and positive")
    app = FastAPI(title="Dwelly case service", version="1", docs_url=None, redoc_url=None)

    def authorize(session: str, authorization: str | None) -> Inbound:
        if not authorization or not authorization.startswith("Bearer "):
            raise HTTPException(401, "Session bearer token required")
        try:
            return store.authenticate(session, authorization.removeprefix("Bearer "))
        except PermissionError as exc:
            raise HTTPException(401, "Invalid or expired session credentials") from exc

    @app.get("/health")
    async def health() -> dict[str, str]:
        return {"status": "ok", "execution": "mock"}

    @app.post("/sessions/{session}/turns")
    async def turn(
        session: str, request: Request, authorization: Annotated[str | None, Header()] = None
    ) -> JSONResponse:
        template = authorize(session, authorization)
        body = bytearray()
        async for chunk in request.stream():
            body.extend(chunk)
            if len(body) > 65536:
                raise HTTPException(413, "Request body too large")
        try:
            payload = Turn.model_validate_json(bytes(body))
        except ValidationError as exc:
            raise HTTPException(422, "Expected request_id and nonempty text only") from exc
        digest = fingerprint(payload.model_dump())
        try:
            replay = store.claim(session, payload.request_id, digest, payload.text, timeout + 5)
        except Conflict as exc:
            raise HTTPException(409, str(exc)) from exc
        except PermissionError as exc:
            raise HTTPException(410, "Session is closed") from exc
        if replay:
            status, result = replay
            return JSONResponse(result, status_code=status, headers={"X-Dwelly-Replayed": "true"})
        # Client supplies neither scope, caller identity, route, timestamp nor authentication state.
        data = template.model_dump(mode="json")
        data.update(
            event_id=fingerprint([session, payload.request_id]),
            text=payload.text,
            received_at=datetime.now(UTC).isoformat(),
        )
        if data["channel"] == "call":
            data.update(session_id=session, active=True)
        event = inbound_adapter.validate_python(data)
        status = 200
        try:
            async with asyncio.timeout(timeout):
                result = await backend(event, session, payload.request_id)
            if not store.active(session):
                status, result = (
                    410,
                    {"status": "failed", "error": "Session closed during processing"},
                )
        except TimeoutError:
            status, result = (
                504,
                {"status": "failed", "error": "Processing timed out; no completion confirmed"},
            )
        except asyncio.CancelledError:
            store.finish(
                session,
                payload.request_id,
                {"status": "failed", "error": "Processing interrupted"},
                503,
            )
            raise
        except Exception:
            status, result = (
                500,
                {"status": "failed", "error": "Processing failed; no completion confirmed"},
            )
        store.finish(session, payload.request_id, result, status)
        return JSONResponse(result, status_code=status)

    @app.post("/sessions/{session}/close")
    async def close(
        session: str, authorization: Annotated[str | None, Header()] = None
    ) -> dict[str, str]:
        authorize(session, authorization)
        store.close(session)
        return {"status": "closed"}

    # JSON schema is useful to providers without exposing data or credentials.
    @app.get("/turn-schema")
    async def schema() -> dict[str, Any]:
        return Turn.model_json_schema()

    return app
