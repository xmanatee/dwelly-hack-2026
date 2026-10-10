"""Dwelly case folders: complete history parsing, cited sources and no ending summaries."""

from pathlib import Path

import pytest

from dwelly_bot.analysis.discovery import DiscoveryConfig
from dwelly_bot.analysis.dwelly_cases import read_case, to_record

INDEX = """# Case 007: Was the transfer sent?

## Case details

- **Source role:** Bank customer
- **Created:** 2025-07-19 09:00:00 UTC
- **Completed:** 2025-07-19 12:00:00 UTC

## Initial request

Did you send my £420 transfer?

## Overview

SECRET overview.

## Next action at escalation

SECRET next action.

## Outcome

SECRET outcome.

## History

[Read the complete event history](history.md).
"""

HISTORY = """# Case 007 history — Was the transfer sent?

Total events: 2

<a id="event-001"></a>
## 2025-07-19 09:47:00 UTC — event 001

- **Channel:** Secure chat
- **From:** Customer
- **To:** Agent

Has it been sent?
Please check.

<a id="event-002"></a>
## 2025-07-19 10:34:00 UTC — event 002

- **Channel:** Internal note
- **From:** Agent
- **To:** Journal

Checking the journal.
"""


def case_folder(tmp_path: Path, history: str = HISTORY) -> Path:
    folder = tmp_path / "007"
    (folder / "attachments").mkdir(parents=True)
    (folder / "index.md").write_text(INDEX)
    (folder / "history.md").write_text(history)
    (folder / "attachments" / "rows.csv").write_text("date,amount\n2025-07-19,420\n")
    (folder / "attachments" / "photo.png").write_bytes(b"\x89PNG")
    return folder


def test_case_becomes_timed_conversation_without_ending_summaries(tmp_path: Path) -> None:
    case = read_case(case_folder(tmp_path))
    record = to_record(case, "banking")
    assert record.id == "case-007" and record.kind == "conversation"
    assert [s.id for s in record.sources] == [
        "case-007/request",
        "case-007/event-001",
        "case-007/event-002",
        "case-007/attachments/rows.csv",
    ]
    event = record.sources[1]
    assert event.speaker == "Customer" and event.timestamp == "2025-07-19 09:47:00 UTC"
    assert event.text == "[Secure chat] Customer → Agent\nHas it been sent?\nPlease check."
    assert [a["text"] is None for a in case["attachments"]] == [True, False]
    assert "SECRET" not in record.model_dump_json()


def test_history_count_mismatch_is_an_error(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="history events"):
        read_case(case_folder(tmp_path, HISTORY.replace("Total events: 2", "Total events: 3")))


def test_exhaustive_discovery_has_no_sampled_stage() -> None:
    config = DiscoveryConfig(batch_size=5).exhaustive(50)
    assert config.batch_size == 5 and config.taxonomy_labels is None
    assert {
        config.deep_sample,
        config.audit_sample,
        config.flagged_audit,
        config.conflict_pairs,
    } == {50}


def test_full_review_selects_every_record(tmp_path: Path) -> None:
    from dwelly_bot.analysis.discovery import select_review

    records = [
        to_record(read_case(case_folder(tmp_path / str(i))), "banking").model_copy(
            update={"id": f"case-{i}"}
        )
        for i in range(9)
    ]
    geometry: dict[str, list[object]] = {"clusters": [], "assignments": []}
    selected = select_review(records, {}, geometry, limit=len(records), seed=0)
    assert sorted(row["id"] for row in selected) == sorted(r.id for r in records)
