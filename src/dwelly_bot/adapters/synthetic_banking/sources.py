"""Read-only decision-time bank tools. No imports of the generator or evaluation data."""

from __future__ import annotations

import asyncio
import hashlib
import json
import sqlite3
from contextlib import closing
from datetime import datetime
from pathlib import Path

from dwelly_bot.context.collector import ContextQuery, ContextRecord, SourceResult, visible_result


def connect(path: Path) -> sqlite3.Connection:
    db = sqlite3.connect(path.resolve().as_uri() + "?mode=ro", uri=True, timeout=5)
    db.row_factory = sqlite3.Row
    db.execute("PRAGMA query_only=ON")
    return db


class BankSource:
    """A scoped bank-system snapshot, thread, document store or contact directory."""

    def __init__(self, path: Path, name: str, description: str) -> None:
        self.path, self.name = path, name
        self.__doc__ = description

    async def lookup(self, query: ContextQuery) -> SourceResult:
        return await asyncio.to_thread(self._read, query)

    def _read(self, query: ContextQuery) -> SourceResult:
        records: list[ContextRecord] = []
        warnings: list[str] = []
        with closing(connect(self.path)) as db:
            snapshot = db.execute(
                "SELECT s.as_of,b.name FROM snapshots s JOIN banks b USING(bank_id) WHERE scope_id=?",
                (query.scope_id,),
            ).fetchone()
            if snapshot is None or datetime.fromisoformat(snapshot["as_of"]) > query.as_of:
                return SourceResult(warnings=("No authorized snapshot at this decision time.",))

            def add(identifier: str, content: dict[str, object], *, at: str | None = None) -> None:
                records.append(
                    ContextRecord(
                        id=identifier,
                        scope_id=query.scope_id,
                        available_at=datetime.fromisoformat(at or snapshot["as_of"]),
                        source=self.name,
                        kind="note",
                        text=json.dumps(content, ensure_ascii=False, indent=2),
                    )
                )

            if self.name == "contact_directory":
                rows = db.execute(
                    "SELECT * FROM contacts WHERE scope_id=?", (query.scope_id,)
                ).fetchall()
                # Transport hints and explicit focused lookup terms are candidates, not auth.
                hints = query.hints
                supplied = [
                    hints.name,
                    hints.email,
                    hints.phone,
                    hints.customer_id,
                    *hints.references,
                ]
                terms = [v.casefold().strip() for v in supplied if v]
                question = query.question.casefold()
                matched = []
                for row in rows:
                    values = [
                        str(row[k]).casefold() for k in ("contact_id", "name", "email", "phone")
                    ]
                    if any(v == term for v in values for term in terms) or any(
                        v in question for v in values
                    ):
                        matched.append(row)
                for row in matched:
                    add(
                        row["contact_id"],
                        {
                            **dict(row),
                            "bank": snapshot["name"],
                            "provenance": "Local routing fixture; name/actor from visible message; email/phone generated.",
                            "identity_verified": False,
                        },
                    )
                if len(matched) > 1:
                    warnings.append(
                        "Ambiguous contact matches; do not merge or choose an identity."
                    )
                if not matched:
                    warnings.append(
                        "No exact contact match inside this scenario; identity remains unresolved."
                    )
            elif self.name == "case_history":
                for row in db.execute(
                    "SELECT * FROM messages WHERE scope_id=? ORDER BY seq", (query.scope_id,)
                ):
                    add(f"event-{row['seq']}", dict(row), at=row["at"])
            elif self.name == "case_documents":
                for row in db.execute(
                    "SELECT * FROM documents WHERE scope_id=? ORDER BY filename", (query.scope_id,)
                ):
                    add(row["filename"], dict(row), at=row["available_at"])
                    if row["text"] is None:
                        warnings.append(
                            f"Attachment {row['filename']}: {row['extraction_status']}; content not read."
                        )
            elif self.name.startswith("bank_"):
                for row in db.execute(
                    "SELECT query_hint,response_text,fields_available,fields_absent FROM responses "
                    "WHERE scope_id=? AND system_id=? ORDER BY query_hint",
                    (query.scope_id, self.name.removeprefix("bank_")),
                ):
                    identifier = hashlib.sha256(row["query_hint"].encode()).hexdigest()[:16]
                    add(
                        identifier,
                        {
                            "query": row["query_hint"],
                            "response": row["response_text"],
                            "fields_available": json.loads(row["fields_available"]),
                            "fields_absent": json.loads(row["fields_absent"]),
                            "missing_field_policy": "Absent/unlisted fields: no further data returned.",
                        },
                    )
                if not records:
                    warnings.append(
                        f"{self.name}: no response recorded for this case; do not infer a result."
                    )
            else:
                raise ValueError(f"Unknown bank source: {self.name}")
        return visible_result(query, SourceResult(records=tuple(records), warnings=tuple(warnings)))


def bank_sources(dataset: Path) -> tuple[BankSource, ...]:
    """Expose the global system catalogue; only scoped decision evidence can be returned."""
    path = dataset / "state" / "decision.sqlite"
    descriptions = {
        "contact_directory": "Find local contact candidates by exact name, phone, email or contact ID. Not identity proof.",
        "case_history": "Read all visible messages in the case thread, including channel and authentication metadata.",
        "case_documents": "Read available attachment text and explicit extraction gaps; no future attachments.",
    }
    with closing(connect(path)) as db:
        descriptions.update(
            {
                f"bank_{r['system_id']}": r["description"]
                for r in db.execute("SELECT * FROM systems")
            }
        )
    return tuple(BankSource(path, name, description) for name, description in descriptions.items())
