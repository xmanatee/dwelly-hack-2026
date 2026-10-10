"""Read-only file/SQL adapters. Project Nikita's schema at this boundary, not in Planner."""

import asyncio
import re
import sqlite3
from contextlib import closing
from pathlib import Path

from pydantic import TypeAdapter

from dwelly_bot.context.collector import ContextQuery, ContextRecord, SourceResult, visible_result


class JsonSource:
    """Read normalized context records from an explicitly configured JSON file."""

    def __init__(self, path: Path, *, name: str = "records") -> None:
        self.path, self.name = path, name

    async def lookup(self, query: ContextQuery) -> SourceResult:
        content = await asyncio.to_thread(self.path.read_text, encoding="utf-8")
        rows = TypeAdapter(tuple[ContextRecord, ...]).validate_json(content)
        return visible_result(query, SourceResult(records=rows))


class SQLiteSource:
    """Search an authorized case's normalized records/view by literal question terms.

    Required columns: id, scope_id, available_at (ISO 8601), kind, source, text.
    Terms select candidates only. A source record is not proof of customer identity.
    """

    def __init__(
        self, path: Path, *, name: str = "database", table: str = "context_records"
    ) -> None:
        if not re.fullmatch(r"[A-Za-z_][A-Za-z_0-9]*", table):
            raise ValueError("Use a simple configured SQL table/view name")
        self.path, self.name, self.table = path.resolve(), name, table

    async def lookup(self, query: ContextQuery) -> SourceResult:
        return await asyncio.to_thread(self._read, query)

    def _read(self, query: ContextQuery) -> SourceResult:
        terms = tuple(dict.fromkeys(re.findall(r"[\w@.+-]{3,}", query.question.casefold())))[:16]
        condition = " OR ".join("instr(lower(text), ?) > 0" for _ in terms)
        with closing(sqlite3.connect(self.path.as_uri() + "?mode=ro", uri=True, timeout=5)) as db:
            db.row_factory = sqlite3.Row
            db.execute("PRAGMA query_only = ON")
            rows = db.execute(
                f'SELECT id, scope_id, available_at, kind, source, text FROM "{self.table}" '
                "WHERE scope_id = ? AND julianday(available_at) <= julianday(?) "
                + (f"AND ({condition}) " if terms else "")
                + "ORDER BY julianday(available_at), id LIMIT ?",
                (query.scope_id, query.as_of.isoformat(), *terms, query.limit + 1),
            ).fetchall()
        return visible_result(
            query,
            SourceResult(records=tuple(ContextRecord.model_validate(dict(row)) for row in rows)),
        )
