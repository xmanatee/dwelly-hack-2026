"""Explicit retrospective review of public examples; never called by the acting adapter."""

import json
import re
from pathlib import Path
from typing import Any

from dwelly_bot.adapters.banking import TRACK, DevelopmentCase
from dwelly_bot.analysis import AnalysisContext, Report
from dwelly_bot.storage import file_hash


async def build(ctx: AnalysisContext) -> Report:
    original = ctx.data / "original" / TRACK
    files = [ctx.data / "cases.json", *sorted(p for p in original.rglob("*") if p.is_file())]

    def read() -> list[dict[str, Any]]:
        rows = []
        for supplied in json.loads((ctx.data / "cases.json").read_text()):
            case = DevelopmentCase.model_validate(supplied).model_dump()
            folder = original / case["organizer_id"]
            history = (folder / "history.md").read_text()
            headers = list(re.finditer(r"^## .* UTC — event (\d+)\s*$", history, re.M))
            cutoff = case["visible_events"]
            if not 0 < cutoff < len(headers):
                raise ValueError("Retrospective review needs a held-out future")
            attachments = sorted(p for p in (folder / "attachments").rglob("*") if p.is_file())
            rows.append(
                {
                    "id": case["id"],
                    "title": case["id"],
                    "summary": case["request"],
                    "fields": {
                        "Decision after event": cutoff,
                        "Total events": len(headers),
                        "Later events": len(headers) - cutoff,
                        "Original attachments": len(attachments),
                        "Visible attachments": len(case.get("evidence_documents", [])) - 2
                        if "evidence_documents" in case
                        else 0,
                    },
                    "sources": [
                        {
                            "id": case["id"] + "/index",
                            "role": "public",
                            "source": str((folder / "index.md").relative_to(ctx.data)),
                            "text": (folder / "index.md").read_text(),
                        },
                        {
                            "id": case["id"] + "/full-history",
                            "role": "public",
                            "source": str((folder / "history.md").relative_to(ctx.data)),
                            "text": history,
                        },
                        *[
                            {
                                "id": case["id"] + "/" + path.name,
                                "role": "public",
                                "source": str(path.relative_to(ctx.data)),
                                "text": path.read_text()
                                if path.suffix in {".txt", ".csv", ".md"}
                                else f"Original binary document; inspect separately. SHA256 {file_hash(path)}",
                            }
                            for path in attachments
                        ],
                    ],
                }
            )
        return rows

    rows = ctx.cached("banking-retrospective-public-review", {}, read, files=files)
    if ctx.parameters.get("saved_run"):
        bundle = ctx.saved_run()
        path = Path(ctx.parameters["saved_run"])
        ctx.sources["saved_run:" + str(path)] = file_hash(path)
        answers = {case["id"]: case for case in bundle["runs"][0]["cases"]}
        for row in rows:
            case = answers.get(row["id"], {})
            row["fields"]["Saved execution"] = case.get("execution_status", "not assigned")
            row["fields"]["Saved answer"] = case.get("answer", "No answer captured")
    report = Report(
        title="Banking public-case retrospective review",
        subtitle="Developer reference only: this report contains future events and outcomes",
    )
    report.metrics(
        {
            "Cases": len(rows),
            "History events": sum(row["fields"]["Total events"] for row in rows),
            "Original attachments": sum(row["fields"]["Original attachments"] for row in rows),
            "Visible attachments": sum(row["fields"]["Visible attachments"] for row in rows),
        }
    )
    report.text(
        "How to use this review",
        "Inspect index, full original history and attachments to understand the example. "
        "Compare a saved next decision with later evidence, considering acceptable alternatives "
        "and what was knowable at the cutoff. Later actions are recorded examples, not actions "
        "performed by this agent, tool responses to replay, or unique ground-truth labels. "
        "Never feed this retrospective report into the decision-time agent. Text attachments "
        "are displayed; PDF originals need separate inspection. No hidden challenge data or "
        "paid model calls are used.",
        collapsed=False,
    )
    report.table(
        "Case coverage",
        [
            {"Case": row["id"], **{k: v for k, v in row["fields"].items() if k != "Saved answer"}}
            for row in rows
        ],
    )
    report.records("Compare saved decisions with later public evidence", rows)
    return report
