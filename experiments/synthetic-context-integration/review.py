"""Inspect saved local-pipeline captures and render a functional report; no model calls."""

import gzip
import json
from datetime import datetime
from pathlib import Path

from dwelly_bot.reporting import Report, render
from dwelly_bot.storage import file_hash

root = Path(__file__).resolve().parent
report = Report(
    title="Synthetic bank integration",
    subtitle="Three cases, two inspected revisions; functional checks, not Planner quality",
)
report.text(
    "Finding",
    "Both revisions completed three local workflows. The first revealed that model notes could restate routing aliases as bank facts or turn missing simulator data into a negative finding. The revised collector sends only observed records, actual questions and source warnings to Planner. Free-form notes stay in the journal. The Planner is a stub; effects are mock. No baseline acceptance or corpus-wide quality result is claimed.",
    collapsed=False,
)
rows = []
records = []
receipts = {}
for revision in ("initial", "revised"):
    path = root / f"{revision}-captures.json.gz"
    saved = json.loads(gzip.decompress(path.read_bytes()))
    receipts[revision] = {"sha256": file_hash(path), "source_commit": saved["source_commit"]}
    for channel, files in saved["runs"].items():
        context = json.loads(files["context.json"])
        event = json.loads(files["input.json"])
        result = json.loads(files["result.json"])
        journal = [json.loads(line) for line in files["events.jsonl"].splitlines()]
        reads = [
            e for e in journal if e.get("tool") == "read_source" and e.get("status") == "returned"
        ]
        calls = [c for e in journal if e.get("kind") == "context_model_trace" for c in e["costs"]]
        assert all(
            r["scope_id"] == event["scope_id"]
            and datetime.fromisoformat(r["available_at"])
            <= datetime.fromisoformat(event["received_at"])
            for r in context["records"]
        )
        observed = {json.dumps(r, sort_keys=True) for e in reads for r in e["result"]["records"]}
        assert {json.dumps(r, sort_keys=True) for r in context["records"]} == observed
        assert result["status"] == "simulated" and len(result["receipts"]) == 2
        if revision == "revised":
            assert set(context["needs"]) == {
                f"{e['arguments']['source']}: {e['arguments']['question']}" for e in reads
            }
            assert context["warnings"] == [w for e in reads for w in e["result"]["warnings"]]
        rows.append(
            {
                "revision": revision,
                "channel": channel,
                "case": event["scope_id"],
                "model_requests": len(calls),
                "read_calls": len(reads),
                "records": len(context["records"]),
                "cost_estimate_usd": round(sum(c["cost_usd"] for c in calls), 8),
                "status": result["status"],
            }
        )
        records.append(
            {
                "id": f"{revision}-{channel}",
                "title": f"{revision}: {event['scope_id']} / {channel}",
                "summary": event["text"],
                "fields": {
                    "Sources": sorted({r["source"] for r in context["records"]}),
                    "Source commit": saved["source_commit"],
                    "Warnings": context["warnings"],
                },
                "sources": [{"id": "context.md", "text": files["context.md"]}],
            }
        )
report.table(
    "Actual runs",
    rows,
    note="Cost is the configured token-price estimate from the shared ledger, not a provider invoice.",
)
report.records("Inspect exact Planner input", records)
report.receipt = receipts
render(report, root / "report.html")
verification = {
    "purpose": "functional integration only",
    "receipts": receipts,
    "runs": rows,
    "checked": [
        "scope and time",
        "records equal observed source returns",
        "mock outcomes",
        "revised needs equal tool questions",
        "revised warnings come only from sources",
    ],
    "total_cost_estimate_usd": round(sum(r["cost_estimate_usd"] for r in rows), 8),
}
(root / "verification.json").write_text(json.dumps(verification, indent=2) + "\n")
print(json.dumps(verification, indent=2))
