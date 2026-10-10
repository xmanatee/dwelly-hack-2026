import asyncio
import json
import sqlite3
from datetime import UTC, datetime
from pathlib import Path

import pytest

from dwelly_bot.channels.intake import IdentityHints
from dwelly_bot.context.collector import ContextQuery, ContextRecord, SourceResult
from dwelly_bot.context.sources import JsonSource, SQLiteSource


async def test_real_sqlite_projection_filters_scope_time_and_search(tmp_path: Path) -> None:
    path = tmp_path / "data.sqlite"
    rows = [
        ("1", "a", "2026-10-10T09:00:00Z", "note", "db", "File receipt AB-123"),
        ("2", "b", "2026-10-10T09:00:00Z", "note", "db", "Other AB-123"),
        ("3", "a", "2026-10-11T09:00:00Z", "note", "db", "Future AB-123"),
    ]
    with sqlite3.connect(path) as db:
        db.execute("CREATE TABLE context_records(id, scope_id, available_at, kind, source, text)")
        db.executemany("INSERT INTO context_records VALUES(?,?,?,?,?,?)", rows)
    query = ContextQuery(
        scope_id="a",
        as_of=datetime(2026, 10, 10, 10, tzinfo=UTC),
        hints=IdentityHints(),
        question="AB-123",
    )
    result = await SQLiteSource(path).lookup(query)
    assert [r.id for r in result.records] == ["1"]
    data = tmp_path / "data.json"
    data.write_text(
        json.dumps(
            [
                dict(
                    zip(
                        ("id", "scope_id", "available_at", "kind", "source", "text"), r, strict=True
                    )
                )
                for r in rows
            ]
        )
    )
    assert [r.id for r in (await JsonSource(data).lookup(query)).records] == ["1"]


async def test_context_agent_sees_only_guarded_records(tmp_path: Path) -> None:
    from pydantic_ai.messages import ModelMessage, ModelResponse, ToolCallPart
    from pydantic_ai.models.function import AgentInfo, FunctionModel

    from dwelly_bot.budget import BudgetLedger
    from dwelly_bot.context.investigator import AgentInvestigator
    from dwelly_bot.experiments.journal import Journal
    from dwelly_bot.models import BudgetedModel

    seen = 0

    def respond(messages: list[ModelMessage], info: AgentInfo) -> ModelResponse:
        nonlocal seen
        seen += 1
        if seen == 1:
            return ModelResponse(
                parts=[ToolCallPart("read_source", {"source": "db", "question": "AB-123"})]
            )
        assert "FOREIGN SECRET" not in str(messages)
        return ModelResponse(
            parts=[
                ToolCallPart(
                    info.output_tools[0].name, {"needs": ["Receipt for AB-123"], "gaps": []}
                )
            ]
        )

    class Source:
        name = "db"

        async def lookup(self, query: ContextQuery) -> SourceResult:
            assert query.scope_id == "a" and query.question == "AB-123"
            return SourceResult(
                records=tuple(
                    ContextRecord(
                        id=scope,
                        scope_id=scope,
                        available_at=query.as_of,
                        source="db",
                        kind="note",
                        text="Known receipt" if scope == "a" else "FOREIGN SECRET",
                    )
                    for scope in ("a", "b")
                )
            )

    journal = Journal(tmp_path / "events.jsonl")
    model = BudgetedModel(FunctionModel(respond), BudgetLedger(tmp_path / "budget.json"), "test")
    try:
        result = await AgentInvestigator(model).gather(
            ContextQuery(
                scope_id="a",
                as_of=datetime(2026, 10, 10, tzinfo=UTC),
                hints=IdentityHints(),
                question="Has AB-123 arrived?",
            ),
            (Source(),),
            journal,
        )
    finally:
        journal.close()
    assert len(result.records) == 1 and seen == 2
    assert result.needs == ("db: AB-123",)


@pytest.mark.parametrize("failure", ["timeout", "error"])
async def test_agent_keeps_partial_evidence_when_source_unavailable(
    tmp_path: Path, failure: str
) -> None:
    from pydantic_ai.messages import ModelMessage, ModelResponse, ToolCallPart
    from pydantic_ai.models.function import AgentInfo, FunctionModel

    from dwelly_bot.budget import BudgetLedger
    from dwelly_bot.context.investigator import AgentInvestigator
    from dwelly_bot.experiments.journal import Journal
    from dwelly_bot.models import BudgetedModel

    class Source:
        name = "db"

        async def lookup(self, query: ContextQuery) -> SourceResult:
            if query.question == "unavailable":
                if failure == "timeout":
                    await asyncio.sleep(60)
                raise RuntimeError("private connection details")
            return SourceResult(
                records=(
                    ContextRecord(
                        id="known",
                        scope_id=query.scope_id,
                        available_at=query.as_of,
                        kind="note",
                        source=self.name,
                        text="Known evidence",
                    ),
                )
            )

    calls = 0

    def respond(messages: list[ModelMessage], info: AgentInfo) -> ModelResponse:
        nonlocal calls
        calls += 1
        if calls == 1:
            return ModelResponse(
                parts=[
                    ToolCallPart("read_source", {"source": "db", "question": question})
                    for question in ("known", "unavailable")
                ]
            )
        assert "Known evidence" in str(messages) and "unavailable" in str(messages)
        assert "private connection details" not in str(messages)
        return ModelResponse(parts=[ToolCallPart(info.output_tools[0].name, {"needs": []})])

    journal = Journal(tmp_path / "events.jsonl")
    model = BudgetedModel(FunctionModel(respond), BudgetLedger(tmp_path / "budget.json"), "test")
    try:
        from dwelly_bot.contracts import RunConfig

        result = await AgentInvestigator(model, RunConfig(tool_timeout_seconds=0.01)).gather(
            ContextQuery(scope_id="a", as_of=datetime.now(UTC), hints=IdentityHints()),
            (Source(),),
            journal,
            source_timeout=10,
        )
    finally:
        journal.close()
    assert [r.id for r in result.records] == ["known"]
    assert result.warnings == (
        f"Source db unavailable ({'TimeoutError' if failure == 'timeout' else 'RuntimeError'}).",
    )
    assert result.warnings[0] in (tmp_path / "events.jsonl").read_text()


async def test_source_cancellation_is_not_converted_to_missing_data() -> None:
    from dwelly_bot.context.collector import read_source

    class Cancelled:
        name = "cancelled"

        async def lookup(self, query: ContextQuery) -> SourceResult:
            raise asyncio.CancelledError()

    with pytest.raises(asyncio.CancelledError):
        await read_source(
            Cancelled(),
            ContextQuery(scope_id="a", as_of=datetime.now(UTC), hints=IdentityHints()),
            1,
        )
