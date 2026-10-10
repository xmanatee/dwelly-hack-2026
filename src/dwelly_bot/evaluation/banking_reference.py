"""Evaluator-only public examples, verified against the execution's pinned corpus."""

import json
from pathlib import Path
from typing import Any

from dwelly_bot.adapters.banking import TRACK, DevelopmentCase
from dwelly_bot.experiments.provenance import dataset_hash
from dwelly_bot.storage import file_hash


def load_reference(root: Path, bundle: dict[str, Any]) -> dict[str, dict[str, Any]]:
    digest = dataset_hash(root)
    for run in bundle["runs"]:
        if (
            run["manifest"]["dataset"] != "dwelly-banking"
            or run["manifest"]["dataset_hash"] != digest
        ):
            raise ValueError("Public review requires the exact banking execution corpus")
    records = [
        DevelopmentCase.model_validate(row) for row in json.loads((root / "cases.json").read_text())
    ]
    references = {}
    for case in records:
        folder = root / "original" / TRACK / case.organizer_id
        documents = []
        for path in [
            folder / "index.md",
            folder / "history.md",
            *sorted((folder / "attachments").rglob("*")),
        ]:
            if not path.is_file():
                continue
            if path.suffix == ".pdf":
                from pypdf import PdfReader

                pages = [
                    page.extract_text(extraction_mode="layout") for page in PdfReader(path).pages
                ]
                if not pages or any(not page.strip() for page in pages):
                    raise ValueError(f"Public reference PDF needs visual review: {path.name}")
                body = "\n\n".join(f"Page {n}\n{page}" for n, page in enumerate(pages, 1))
            elif path.suffix in {".md", ".csv", ".txt"}:
                body = path.read_text()
            else:
                raise ValueError(f"Unsupported public reference: {path.name}")
            documents.append(
                {"path": str(path.relative_to(root)), "sha256": file_hash(path), "text": body}
            )
        references[case.id] = {
            "role": "Retrospective public example, not a unique ground-truth answer",
            "decision_after_event": case.visible_events,
            "decision_time": case.decision_time,
            "agent_visible_documents": case.evidence_documents,
            "documents": documents,
        }
    assigned = {case["id"] for run in bundle["runs"] for case in run["cases"]}
    if assigned - references.keys():
        raise ValueError("Missing public reference cases")
    return {key: value for key, value in references.items() if key in assigned}
