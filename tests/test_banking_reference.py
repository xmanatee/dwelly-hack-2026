"""Retrospective grading cannot silently use another corpus or missing references."""

import json
from pathlib import Path
from typing import Any

import pytest

from dwelly_bot.evaluation import banking_reference


def test_reference_requires_matching_corpus_and_keeps_cutoff(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(banking_reference, "dataset_hash", lambda _: "pinned")
    row = dict(
        id="banking-001",
        organizer_id="001",
        track="Banking & Financial Services",
        split="development",
        request="Help",
        decision_time="2025-01-01 02:00:00 UTC",
        visible_events=2,
        sources=[],
    )
    (tmp_path / "cases.json").write_text(json.dumps([row]))
    original = tmp_path / "original" / "Banking & Financial Services" / "001"
    original.mkdir(parents=True)
    (original / "index.md").write_text("Example outcome")
    (original / "history.md").write_text("Earlier events and later evidence")
    bundle: dict[str, Any] = {
        "runs": [
            {
                "manifest": {"dataset": "dwelly-banking", "dataset_hash": "pinned"},
                "cases": [{"id": "banking-001"}],
            }
        ]
    }
    refs = banking_reference.load_reference(tmp_path, bundle)
    assert refs["banking-001"]["decision_after_event"] == 2
    assert len(refs["banking-001"]["documents"]) == 2
    bundle["runs"][0]["manifest"]["dataset_hash"] = "other"
    with pytest.raises(ValueError, match="exact banking execution corpus"):
        banking_reference.load_reference(tmp_path, bundle)
    bundle["runs"][0]["manifest"]["dataset_hash"] = "pinned"
    bundle["runs"][0]["cases"].append({"id": "banking-002"})
    with pytest.raises(ValueError, match="Missing public reference"):
        banking_reference.load_reference(tmp_path, bundle)
