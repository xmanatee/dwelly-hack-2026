"""Explore visible banking requests; completed histories and evaluation data stay closed."""

import json
from collections import Counter
from typing import Any

from dwelly_bot.analysis import AnalysisContext, Report, Table
from dwelly_bot.analysis.charts import ranking
from dwelly_bot.analysis.exploration import add_saved_run, add_text_analysis


async def build(ctx: AnalysisContext) -> Report:
    files = [ctx.data / "cases.json", *sorted((ctx.data / "documents").rglob("*.md"))]

    def read() -> dict[str, Any]:
        return {
            "cases": json.loads(files[0].read_text()),
            "documents": [
                {
                    "id": str(p.relative_to(ctx.data)),
                    "case_id": p.relative_to(ctx.data / "documents").parts[0],
                    "text": p.read_text(),
                    "lines": len(p.read_text().splitlines()),
                }
                for p in files[1:]
            ],
        }

    data = ctx.cached("banking-visible-evidence", {}, read, files=files)
    cases, documents = data["cases"], data["documents"]
    for row in cases:
        row["sources"] = [
            {
                "id": row["id"] + "/request",
                "text": row["request"],
                "source": "documents/" + row["id"] + "/request.md",
                "role": "public",
            }
        ]
    report = Report(
        title="Banking development cases",
        subtitle="Initial requests and evidence at each declared decision point",
    )
    report.metrics(
        {"Cases": len(cases), "Visible documents": len(documents), "Trusted outcome labels": 0}
    )
    channels: Counter[str] = Counter()
    for row in documents:
        for line in row["text"].splitlines():
            if line.startswith("- **Channel:** "):
                channels[line.removeprefix("- **Channel:** ")] += 1
    report.text(
        "Findings and limits",
        f"{len(cases)} public development cases have a request and an explicitly bounded history prefix. Later events and overview/outcome summaries are excluded. Reviewed snapshots may include attachments available at the cutoff; the historical v1 baseline excluded them all. The {sum(channels.values())} visible events describe observed context; they do not establish that the requested bank action succeeded. Channel counts count events, not customers. Repeated fictional names must not join cases. The separate banking_review recipe supports retrospective study of complete public examples without exposing future evidence to this agent view.",
    )
    report.chart(
        "Visible event channels",
        ranking(
            [{"channel": channel, "count": count} for channel, count in channels.items()],
            "channel",
            unit="Events",
        ),
    )
    await add_text_analysis(
        report,
        ctx,
        Table("requests", cases),
        text="request",
        id_column="id",
        title="Inspect development requests",
        source_kind="question",
    )
    report.records(
        "Evidence boundary examples",
        [
            {
                "id": row["id"],
                "title": row["id"],
                "summary": row["request"],
                "fields": {
                    "Decision time": row["decision_time"],
                    "Visible events": row["visible_events"],
                    "Split": row["split"],
                },
                "sources": row["sources"],
            }
            for row in cases
            if row["organizer_id"] in {"001", "035", "039"}
        ],
    )
    add_saved_run(report, ctx)
    return report
