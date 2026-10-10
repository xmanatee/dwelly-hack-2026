"""Durable trusted bindings and request receipts; no provider recording or audio storage."""

import hashlib
import json
import secrets
import sqlite3
import time
from contextlib import closing
from pathlib import Path
from typing import Any

from dwelly_bot.channels.intake import CallInput, Inbound, inbound_adapter


class Conflict(ValueError):
    pass


class SessionStore:
    def __init__(self, path: Path) -> None:
        self.path = path
        path.parent.mkdir(parents=True, exist_ok=True)
        with closing(self.connect()) as db, db:
            db.executescript("""
                CREATE TABLE IF NOT EXISTS sessions (
                    id TEXT PRIMARY KEY, token_hash TEXT NOT NULL, event TEXT NOT NULL,
                    expires REAL NOT NULL, active INTEGER NOT NULL DEFAULT 1);
                CREATE TABLE IF NOT EXISTS turns (
                    session TEXT NOT NULL, id TEXT NOT NULL, digest TEXT NOT NULL,
                    started REAL NOT NULL, deadline REAL NOT NULL, text TEXT NOT NULL,
                    status TEXT NOT NULL, result TEXT, http_status INTEGER,
                    PRIMARY KEY(session,id));
            """)
        path.chmod(0o600)

    def connect(self) -> sqlite3.Connection:
        db = sqlite3.connect(self.path, timeout=10)
        db.row_factory = sqlite3.Row
        return db

    def create(self, event: Inbound, ttl: int = 3600) -> tuple[str, str]:
        if isinstance(event, CallInput) and not event.active:
            raise ValueError("Cannot bind an inactive call")
        if not 1 <= ttl <= 86400:
            raise ValueError("Session TTL must be between 1 and 86400 seconds")
        session, token = secrets.token_urlsafe(24), secrets.token_urlsafe(32)
        with closing(self.connect()) as db, db:
            db.execute(
                "INSERT INTO sessions(id,token_hash,event,expires) VALUES (?,?,?,?)",
                (
                    session,
                    hashlib.sha256(token.encode()).hexdigest(),
                    event.model_dump_json(),
                    time.time() + ttl,
                ),
            )
        return session, token

    def authenticate(self, session: str, token: str) -> Inbound:
        with closing(self.connect()) as db:
            row = db.execute("SELECT * FROM sessions WHERE id=?", (session,)).fetchone()
        candidate = hashlib.sha256(token.encode()).hexdigest()
        if (
            row is None
            or not secrets.compare_digest(row["token_hash"], candidate)
            or row["expires"] <= time.time()
        ):
            raise PermissionError("Invalid or expired session credentials")
        return inbound_adapter.validate_json(row["event"])

    def active(self, session: str) -> bool:
        with closing(self.connect()) as db:
            row = db.execute(
                "SELECT active,expires FROM sessions WHERE id=?", (session,)
            ).fetchone()
        return bool(row and row["active"] and row["expires"] > time.time())

    def close(self, session: str) -> None:
        with closing(self.connect()) as db, db:
            db.execute("UPDATE sessions SET active=0 WHERE id=?", (session,))

    def claim(
        self, session: str, request: str, digest: str, text: str, timeout: float
    ) -> tuple[int, dict[str, Any]] | None:
        now = time.time()
        with closing(self.connect()) as db, db:
            db.execute("BEGIN IMMEDIATE")
            # Expired work is marked failed, never silently executed again after restart.
            db.execute(
                "UPDATE turns SET status='failed',http_status=504,result=? WHERE session=? AND status='running' AND deadline<=?",
                (
                    json.dumps(
                        {
                            "status": "failed",
                            "error": "Request interrupted or timed out; review before submitting a new request.",
                        }
                    ),
                    session,
                    now,
                ),
            )
            prior = db.execute(
                "SELECT * FROM turns WHERE session=? AND id=?", (session, request)
            ).fetchone()
            if prior:
                if prior["digest"] != digest:
                    raise Conflict("Request ID reused with different input")
                if prior["status"] == "running":
                    raise Conflict("Request is still running")
                return prior["http_status"], json.loads(prior["result"])
            state = db.execute(
                "SELECT active,expires FROM sessions WHERE id=?", (session,)
            ).fetchone()
            if state is None or not state["active"] or state["expires"] <= now:
                raise PermissionError("Session is closed or expired")
            if db.execute(
                "SELECT 1 FROM turns WHERE session=? AND status='running'", (session,)
            ).fetchone():
                raise Conflict("Another turn is still running in this session")
            db.execute(
                "INSERT INTO turns VALUES (?,?,?,?,?,?,'running',NULL,NULL)",
                (session, request, digest, now, now + timeout, text),
            )
        return None

    def finish(self, session: str, request: str, result: dict[str, Any], status: int = 200) -> None:
        with closing(self.connect()) as db, db:
            db.execute(
                "UPDATE turns SET status=?,result=?,http_status=? WHERE session=? AND id=? AND status='running'",
                (
                    "complete" if status == 200 else "failed",
                    json.dumps(result),
                    status,
                    session,
                    request,
                ),
            )

    def history(self, session: str) -> list[dict[str, Any]]:
        with closing(self.connect()) as db:
            rows = db.execute(
                "SELECT id,text,started FROM turns WHERE session=? AND status='complete' ORDER BY started DESC LIMIT 20",
                (session,),
            ).fetchall()
        return [dict(row) for row in reversed(rows)]

    def binding(self, session: str) -> Inbound:
        """Internal trusted binding lookup; never exposed as an unauthenticated HTTP route."""
        with closing(self.connect()) as db:
            row = db.execute("SELECT event FROM sessions WHERE id=?", (session,)).fetchone()
        if row is None:
            raise ValueError("Unknown session")
        return inbound_adapter.validate_json(row["event"])
