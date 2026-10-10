"""Decision-time evidence follows the public corpus contract, not a hidden answer key."""

import json
import runpy
from pathlib import Path
from typing import Any

import pytest

from dwelly_bot.adapters.banking import BankingAdapter, DevelopmentCase
from dwelly_bot.adapters.banking_data import (
    AttachmentAvailability,
    DecisionProfile,
    visible_attachments,
)
from dwelly_bot.contracts import AgentCase, RunConfig
from dwelly_bot.experiments.provenance import dataset_hash
from dwelly_bot.paths import DATASET, ROOT
from dwelly_bot.reporting.submission import check_destination, export


def history() -> str:
    return "\n".join(
        f"## 2025-01-01 0{n}:00:00 UTC — event {n:03}\n\n{text}\n"
        for n, text in enumerate(
            ["Uploaded batch.csv", "Check bank receipt", "receipt.txt now available"], 1
        )
    )


def rule(path: str, event: int) -> AttachmentAvailability:
    return AttachmentAvailability(path=path, available_after_event=event, basis="Reviewed event")


def test_availability_is_not_filename_or_document_date(tmp_path: Path) -> None:
    folder = tmp_path / "attachments"
    folder.mkdir()
    (folder / "batch.csv").write_text("amount\n420\n")
    (folder / "receipt.txt").write_text("Dated last year; FUTURE_RECEIPT")
    rules = [rule("attachments/batch.csv", 1), rule("attachments/receipt.txt", 3)]
    documents = visible_attachments(tmp_path, history(), 2, rules)
    assert set(documents) == {"attachments/batch.csv.md"}
    assert "420" in documents["attachments/batch.csv.md"]
    assert "FUTURE_RECEIPT" not in json.dumps(documents)
    with pytest.raises(ValueError, match="Every original attachment"):
        visible_attachments(tmp_path, history(), 2, rules[:1])
    with pytest.raises(ValueError, match="does not identify"):
        visible_attachments(tmp_path, history(), 2, [rule("attachments/receipt.txt", 1)])


def test_unsupported_available_media_and_escaping_paths_fail(tmp_path: Path) -> None:
    (tmp_path / "attachments").mkdir()
    (tmp_path / "attachments/record.pdf").write_bytes(b"%PDF-fixture")
    source = history().replace("batch.csv", "record.pdf")
    with pytest.raises(ValueError, match="supported media reader"):
        visible_attachments(tmp_path, source, 2, [rule("attachments/record.pdf", 1)])
    with pytest.raises(ValueError, match="case-local"):
        rule("attachments/../../secret.txt", 1)
    outside = tmp_path / "sibling/secret.txt"
    outside.parent.mkdir()
    outside.write_text("outside attachment")
    (tmp_path / "attachments/record.pdf").unlink()
    (tmp_path / "attachments/record.pdf").symlink_to(outside)
    # An attachment may not point outside its owning case.
    case = tmp_path / "case"
    case.mkdir()
    (tmp_path / "attachments").rename(case / "attachments")
    with pytest.raises(ValueError, match="escaping"):
        visible_attachments(case, source, 2, [rule("attachments/record.pdf", 1)])


def installed_case(root: Path) -> AgentCase:
    row = {
        "id": "banking-001",
        "organizer_id": "001",
        "track": "Banking & Financial Services",
        "split": "development",
        "request": "Check receipt",
        "visible_events": 2,
        "decision_time": "2025-01-01 02:00:00 UTC",
        "sources": [],
    }
    (root / "cases.json").write_text(json.dumps([row]))
    folder = root / "documents/banking-001"
    folder.mkdir(parents=True)
    (folder / "request.md").write_text("Check receipt")
    (folder / "history.md").write_text(history().split("## 2025-01-01 03:")[0])
    return BankingAdapter().load_cases(root)[0]


def test_adapter_rejects_future_events_and_extra_reference_documents(tmp_path: Path) -> None:
    case = installed_case(tmp_path)
    adapter = BankingAdapter()
    adapter.prepare(case, tmp_path, RunConfig())
    folder = tmp_path / "documents/banking-001"
    (folder / "history.md").write_text(history())
    with pytest.raises(ValueError, match="decision point"):
        adapter.prepare(case, tmp_path, RunConfig())
    (folder / "outcome.md").write_text("FUTURE_RECEIPT")
    with pytest.raises(ValueError, match="inventory"):
        adapter.prepare(case, tmp_path, RunConfig())


def test_challenge_split_cannot_be_relabelled_as_public_data(tmp_path: Path) -> None:
    installed_case(tmp_path)
    row = json.loads((tmp_path / "cases.json").read_text())[0]
    row["split"] = "reality_test"
    with pytest.raises(ValueError):
        DevelopmentCase.model_validate(row)
    row["split"] = "development"
    row["id"] = "banking-002"
    with pytest.raises(ValueError, match="identity"):
        DevelopmentCase.model_validate(row)


def test_nested_attachment_citations_must_have_been_read(tmp_path: Path) -> None:
    case = AgentCase("banking-041", "dwelly-banking", "Fixture", {})
    capture: dict[str, Any] = {
        "execution_status": "completed",
        "answer": "Receipt is unconfirmed.",
        "public_rationale": "attachments/batch-041.csv.md:L1",
        "tool_events": [
            {
                "tool": "read_document",
                "status": "returned",
                "result": {"document": "attachments/batch-041.csv.md", "text": "1: Staff A,420.00"},
            }
        ],
    }
    adapter = BankingAdapter()
    assert (
        adapter.grade_saved(case, tmp_path, RunConfig(), capture)["checks"][2]["status"] == "pass"
    )
    capture["public_rationale"] = "batch-041.csv.md:L1"
    assert (
        adapter.grade_saved(case, tmp_path, RunConfig(), capture)["checks"][2]["status"] == "fail"
    )


def test_public_exports_cannot_masquerade_as_reality_test(tmp_path: Path) -> None:
    saved = {
        "schema_version": 1,
        "runs": [
            {
                "id": "public",
                "manifest": {"dataset": "dwelly-banking", "assigned_case_ids": ["banking-041"]},
                "cases": [
                    {
                        "id": "banking-041",
                        "execution_status": "completed",
                        "answer": "Original answer",
                    }
                ],
            }
        ],
    }
    with pytest.raises(ValueError, match="Public development"):
        check_destination(tmp_path / "ANSWERS", dataset="dwelly-banking")
    with pytest.raises(ValueError, match="Public development"):
        export(saved, tmp_path / "ANSWERS")
    assert not (tmp_path / "ANSWERS").exists()
    export(saved, tmp_path / "development-review")
    assert "Do not submit" in (tmp_path / "development-review/README.md").read_text()
    assert (tmp_path / "development-review/1/ANSWER.md").read_text() == "Original answer\n"


def test_reviewed_profile_builds_without_changing_legacy_corpus(tmp_path: Path) -> None:
    archive = DATASET / "release.zip"
    if not archive.exists():
        pytest.skip("Optional pinned original archive not installed")
    before = dataset_hash(DATASET)
    profile = DecisionProfile.model_validate_json(
        (ROOT / "configs/banking-development.json").read_text()
    )
    # Different cutoffs are explicit per case; 042's text report is known at event 004.
    profile.after_event = {"001": 4, "042": 4}
    install = runpy.run_path(str(ROOT / "dataset/fetch.py"))["install"]
    root = tmp_path / "reviewed"
    install(root, archive, profile)
    fingerprint = dataset_hash(root)
    adapter = BankingAdapter()
    cases = {case.id: case for case in adapter.load_cases(root)}
    assert len(cases) == 50
    for case in cases.values():
        adapter.prepare(case, root, RunConfig())
    assert cases["banking-001"].input["visible_events"] == 4
    assert "event 005" not in (root / "documents/banking-001/history.md").read_text()
    assert (root / "documents/banking-041/attachments/batch-041.csv.md").exists()
    assert (root / "documents/banking-042/attachments/validation-042.txt.md").exists()
    assert not (root / "documents/banking-039/attachments").exists()
    for original in (DATASET / "original").rglob("*"):
        if original.is_file():
            assert original.read_bytes() == (root / original.relative_to(DATASET)).read_bytes()
    install(root, archive, profile)
    assert dataset_hash(root) == fingerprint and dataset_hash(DATASET) == before
    profile.after_event = {"001": 3}
    with pytest.raises(ValueError, match="profile differs"):
        install(root, archive, profile)
