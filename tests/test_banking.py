"""Leakage boundaries, retrieval and observable-only saved checks."""

import json
from pathlib import Path

import pytest
from pydantic_ai import ModelRetry

from dwelly_bot.adapters.banking import BankingAdapter, initial_view
from dwelly_bot.context.documents import Documents
from dwelly_bot.contracts import RunConfig
from dwelly_bot.paths import DATASET


def test_cutoff_excludes_titles_summaries_later_events_and_counts() -> None:
    index = (
        "# OUTCOME_SECRET\n\n## Initial request\n\nPlease check my payment.\n\n## Outcome\nSECRET\n"
    )
    history = "# OUTCOME_SECRET\nTotal events: 3\n" + "\n".join(
        f'<a id="event-{n:03}"></a>\n## 2025-01-01 0{n}:00:00 UTC — event {n:03}\n\n'
        + ("SECRET" if n == 3 else f"Observed {n}")
        for n in range(1, 4)
    )
    request, visible, stamp = initial_view(index, history)
    assert request == "Please check my payment."
    assert "SECRET" not in visible and "Total events" not in visible and "event-003" not in visible
    assert "Observed 1" in visible and "Observed 2" in visible
    assert stamp == "2025-01-01 02:00:00 UTC"
    with pytest.raises(ValueError):
        initial_view(index, history.replace("event 002", "event 009"))


def test_document_boundary_and_pagination(tmp_path: Path) -> None:
    docs = tmp_path / "documents"
    docs.mkdir()
    (docs / "evidence.md").write_text("one\nmatch A\nmatch B\nlast\n")
    (tmp_path / "outcomes.md").write_text("PRIVATE_REFERENCE")
    store = Documents(docs)
    with pytest.raises(ModelRetry):
        store.read_document("../outcomes.md")
    assert store.read_document("evidence.md", limit=2)["next_line"] == 3
    assert "last" in store.read_document("evidence.md", start_line=3)["text"]
    hits = store.search_documents("match", limit=1)
    assert hits["total_matches"] == 2 and hits["next_offset"] == 1
    assert store.search_documents("match", limit=1, offset=1)["matches"][0]["line"] == 3
    (docs / "escaped.md").symlink_to(tmp_path / "outcomes.md")
    with pytest.raises(ValueError, match="escapes"):
        Documents(docs)


def test_actual_development_boundaries() -> None:
    if not (DATASET / "cases.json").exists():
        pytest.skip("Optional dataset not installed")
    adapter = BankingAdapter()
    cases = adapter.load_cases(DATASET)
    assert len(cases) == 50
    assert cases[0].id == "banking-001" and cases[-1].id == "banking-050"
    for case in cases:
        session = adapter.prepare(case, DATASET, RunConfig())
        names = {r["document"] for r in session.documents.list_documents()}
        assert names == {"request.md", "history.md"}
        history = session.documents.read_document("history.md")["text"]
        assert "event 003" not in history and "Total events" not in history
        assert case.metadata["split"] == "development"
        with pytest.raises(ModelRetry):
            session.documents.read_document("../../original/index.md")
    with pytest.raises(ValueError, match="Unknown case"):
        adapter.load_cases(DATASET, ["banking-999"])


def test_saved_checks_never_invent_correctness(tmp_path: Path) -> None:
    from dwelly_bot.contracts import AgentCase

    case = AgentCase("banking-001", "dwelly-banking", "Fixture", {})
    adapter = BankingAdapter()
    row = {
        "execution_status": "completed",
        "answer": "Needs bank record.",
        "public_rationale": "history.md:L1-L2",
        "tool_events": [
            {
                "tool": "read_document",
                "status": "returned",
                "result": {
                    "document": "history.md",
                    "text": "1: Payment authorised\n2: Receipt unknown",
                },
            }
        ],
    }
    checked = adapter.grade_saved(case, tmp_path, RunConfig(), row)
    assert checked["goal_pass"] is None
    assert [c["status"] for c in checked["checks"]] == ["pass", "pass", "pass", "unknown"]
    row["public_rationale"] = "history.md:L99"
    checked = adapter.grade_saved(case, tmp_path, RunConfig(), row)
    assert checked["checks"][2]["status"] == "fail"
    assert "expected" not in json.dumps(checked)
