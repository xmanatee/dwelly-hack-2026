"""Inventory active Planner instructions; source review, never an accuracy benchmark."""

from __future__ import annotations

import json
import re
from pathlib import Path

from dwelly_bot.reporting.models import Report
from dwelly_bot.reporting.page import render
from dwelly_bot.storage import file_hash, save_json

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / "src/dwelly_bot/planner"
OUTPUT = ROOT / "analysis/artifacts/planner-generalization"


def main() -> None:
    catalog = json.loads((BASE / "skills/catalog.json").read_text())
    paths = (
        sorted(BASE.rglob("*.md"))
        + sorted(BASE.rglob("*.json"))
        + [BASE / name for name in ("planner.py", "skills.py", "validate.py", "contracts.py")]
    )
    paths += [ROOT / "src/hackathon_winner/adapters.py", ROOT / "src/dwelly_bot/harness/runtime.py"]
    records = []
    for path in paths:
        content = path.read_text()
        records.append(
            {
                "path": str(path.relative_to(ROOT)),
                "sha256": file_hash(path),
                "text": content,
                "words": len(content.split()),
            }
        )
    skills = []
    for entry in catalog:
        path = BASE / "skills" / entry["id"] / "SKILL.md"
        content = path.read_text()
        frontmatter = content.split("---", 2)[1].splitlines()
        fields = dict(line.split(": ", 1) for line in frontmatter if ": " in line)
        if fields["name"] != entry["id"] or fields["description"] != entry["description"]:
            raise ValueError(f"Catalog/frontmatter mismatch: {entry['id']}")
        # Deliberately narrow, disclosed scan. No claim to detect semantic memorization.
        markers = re.findall(r"\b(?:\d{3}-e\d{3}|SYN-\d{4}|HV-\d{3})\b", content)
        skills.append(
            {
                "id": entry["id"],
                "words": len(content.split()),
                "case_marker_matches": markers,
                "catalog_matches": True,
            }
        )
    review = Path(__file__).with_name("README.md")
    data = {
        "source_hashes": {r["path"]: r["sha256"] for r in records},
        "review_sha256": file_hash(review),
        "skills": skills,
        "sources": records,
        "scope": "Source audit; no behavioral pass/fail results",
        "new_model_calls": 0,
    }
    OUTPUT.mkdir(parents=True, exist_ok=True)
    save_json(OUTPUT / "inventory.json", data, overwrite=True)
    report = Report(
        title="Planner generalization audit",
        subtitle="Source review, not an unseen-case accuracy result",
    )
    report.metrics(
        {"Skills inspected": len(skills), "Source files": len(records), "New model calls": 0}
    )
    report.text("Assessment and proposed improvements", review.read_text(), collapsed=False)
    report.table(
        "Catalog consistency and literal marker scan",
        skills,
        note="Zero matches does not establish absence of semantic overfitting. See the manual review.",
    )
    report.records(
        "Exact reviewed sources",
        [
            {
                "id": r["path"],
                "title": r["path"],
                "fields": {"SHA256": r["sha256"]},
                "sources": [{"id": r["path"], "source": r["path"], "text": r["text"]}],
            }
            for r in records
        ],
    )
    report.receipt = {
        "source_audit": True,
        "source_hashes": data["source_hashes"],
        "review_sha256": data["review_sha256"],
        "new_model_calls": 0,
    }
    save_json(OUTPUT / "report.json", report.model_dump(mode="json"), overwrite=True)
    render(report, OUTPUT / "report.html")
    print(OUTPUT / "report.html")


if __name__ == "__main__":
    main()
