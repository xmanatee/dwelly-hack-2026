"""Explicit tables and relationships, independent of case execution and grading."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Literal

from dwelly_bot.contracts import JsonRecord


@dataclass
class Table:
    name: str
    rows: list[JsonRecord]
    id_column: str | None = None
    role: Literal["public", "historical", "evaluation_only"] = "public"
    notes: str = ""
    columns: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        if not self.columns:
            self.columns = sorted({key for row in self.rows for key in row})

    def require(self, *columns: str) -> None:
        missing = set(columns) - set(self.columns)
        if missing:
            raise ValueError(f"{self.name}: missing columns {sorted(missing)}")


@dataclass(frozen=True)
class Relationship:
    child: str
    child_key: str
    parent: str
    parent_key: str


def relationships(tables: list[Table], links: list[Relationship]) -> list[JsonRecord]:
    by_name = {table.name: table for table in tables}
    if len(by_name) != len(tables):
        raise ValueError("Table names must be unique")
    checks: list[JsonRecord] = []
    for link in links:
        child, parent = by_name[link.child], by_name[link.parent]
        child.require(link.child_key)
        parent.require(link.parent_key)
        keys = Counter(row.get(link.parent_key) for row in parent.rows)
        duplicate = sum(count - 1 for key, count in keys.items() if key is not None and count > 1)
        absent = sum(
            row.get(link.child_key) is not None and row.get(link.child_key) not in keys
            for row in child.rows
        )
        nulls = sum(row.get(link.child_key) is None for row in child.rows)
        checks.append(
            {
                "relationship": f"{child.name}.{link.child_key} → {parent.name}.{link.parent_key}",
                "duplicate_parent_keys": duplicate,
                "unmatched_children": absent,
                "missing_child_keys": nulls,
                "status": "review" if duplicate or absent or nulls else "ok",
            }
        )
    return checks


def enrich(child: Table, parent: Table, child_key: str, parent_key: str, prefix: str) -> Table:
    """Explicit many-to-one join; refuse ambiguous parents instead of multiplying rows."""
    if parent.role == "evaluation_only" and child.role != "evaluation_only":
        raise ValueError("Evaluation-only parents cannot enrich source tables")
    child.require(child_key)
    parent.require(parent_key)
    index: dict[Any, JsonRecord] = {}
    for row in parent.rows:
        key = row.get(parent_key)
        if key is None or key in index:
            raise ValueError(f"{parent.name}.{parent_key} must contain unique non-null keys")
        index[key] = row
    rows = []
    for row in child.rows:
        extra = {prefix + key: value for key, value in index.get(row.get(child_key), {}).items()}
        if set(extra) & set(row):
            raise ValueError("Join prefix collides with a child column")
        rows.append({**row, **extra})
    return Table(child.name, rows, child.id_column, child.role, child.notes)


def threads(
    messages: Table,
    *,
    case_id: str,
    message_id: str,
    text: str,
    timestamp: str,
    speaker: str,
) -> Table:
    """Whole-thread analysis with stable message citations and explicit chronology."""
    messages.require(case_id, message_id, text, timestamp, speaker)
    grouped: dict[str, list[tuple[datetime, JsonRecord]]] = {}
    seen: set[str] = set()
    for row in messages.rows:
        identifier = f"{row[case_id]}/{row[message_id]}"
        if identifier in seen or row[case_id] in {None, ""} or row[message_id] in {None, ""}:
            raise ValueError("Thread/message IDs must be present and unique")
        seen.add(identifier)
        when = datetime.fromisoformat(str(row[timestamp]))
        if when.tzinfo is None:
            raise ValueError("Message timestamps require an explicit timezone")
        grouped.setdefault(str(row[case_id]), []).append((when, row))
    records = []
    for identifier, entries in sorted(grouped.items()):
        ordered = [row for _, row in sorted(entries, key=lambda entry: entry[0])]
        records.append(
            {
                "id": identifier,
                "message_count": len(ordered),
                "text": "\n".join(
                    f"{row[timestamp]} · {row[speaker]}: {row[text]}" for row in ordered
                ),
                "sources": [
                    {
                        "id": f"{identifier}/{row[message_id]}",
                        "text": str(row[text]),
                        "source": messages.name,
                        "role": messages.role,
                        "speaker": str(row[speaker]),
                        "timestamp": str(row[timestamp]),
                    }
                    for row in ordered
                ],
            }
        )
    return Table(messages.name + "_threads", records, "id", messages.role)
