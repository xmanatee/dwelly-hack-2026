from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from dwelly_bot.channels.intake import (
    CallInput,
    EmailInput,
    IdentityHints,
    TicketInput,
    normalize,
)
from dwelly_bot.context.collector import (
    ContextCollector,
    ContextQuery,
    ContextRecord,
    InMemorySource,
    SourceResult,
)

NOW = datetime(2026, 10, 10, tzinfo=UTC)


def test_transport_routes_preserve_thread_and_live_call() -> None:
    common = dict(event_id="e", scope_id="case-a", received_at=NOW, text="Help")
    email = normalize(
        EmailInput.model_validate(
            {**common, "sender": "sender@example.test", "thread_id": "thread"}
        )
    )
    call = normalize(
        CallInput.model_validate(
            {**common, "caller": "+44000", "session_id": "call", "active": False}
        )
    )
    ticket = normalize(TicketInput.model_validate({**common, "ticket_id": "ticket"}))
    assert email.reply_route.model_dump() == dict(
        channel="email", recipient="sender@example.test", thread_id="thread"
    )
    assert call.reply_route.model_dump() == dict(channel="call", session_id="call", active=False)
    assert ticket.reply_route.model_dump() == dict(channel="ticket", ticket_id="ticket")


async def test_context_filters_future_and_other_cases_even_if_source_misbehaves(
    tmp_path: Path,
) -> None:
    records = tuple(
        ContextRecord(
            id=str(i), scope_id=scope, available_at=at, kind="note", source="db", text=text
        )
        for i, (scope, at, text) in enumerate(
            [
                ("case-a", NOW, "Known entry"),
                ("case-a", NOW + timedelta(seconds=1), "FUTURE SECRET"),
                ("case-b", NOW, "OTHER CUSTOMER"),
            ]
        )
    )

    class OverbroadSource:
        name = "db"

        async def lookup(self, query: ContextQuery) -> SourceResult:
            return SourceResult(records=records)

    trigger = normalize(
        TicketInput(
            event_id="e",
            scope_id="case-a",
            received_at=NOW,
            text="Check reference AB-123",
            ticket_id="t",
            hints=IdentityHints(name="Same Name"),
        )
    )
    result = await ContextCollector((OverbroadSource(),)).collect(
        trigger, capabilities="mock handoff"
    )
    assert len(result.records) == 1
    assert "Known entry" in result.text
    assert "FUTURE SECRET" not in result.text and "OTHER CUSTOMER" not in result.text
    assert result.hints.references == ("AB-123",)
    path = tmp_path / "context.md"
    result.write(path)
    assert path.read_text() == result.text
    with pytest.raises(FileExistsError):
        result.write(path)


async def test_source_failure_is_visible_and_other_sources_still_contribute() -> None:
    class BrokenSource:
        name = "customers"

        async def lookup(self, query: ContextQuery) -> SourceResult:
            raise OSError("private connection details")

    record = ContextRecord(
        id="1", scope_id="s", available_at=NOW, source="events", kind="event", text="An event"
    )
    trigger = normalize(
        TicketInput(event_id="e", scope_id="s", received_at=NOW, text="Help", ticket_id="t")
    )
    result = await ContextCollector((BrokenSource(), InMemorySource((record,)))).collect(
        trigger, capabilities="mock"
    )
    assert "An event" in result.text
    assert "customers unavailable" in result.text
    assert "private connection" not in result.text
