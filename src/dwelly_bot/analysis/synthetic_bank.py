"""Profile runtime evidence only; never open labels or retrospective entity state."""

from contextlib import closing
from typing import Any

from dwelly_bot.adapters.synthetic_banking.sources import connect
from dwelly_bot.analysis import AnalysisContext, Report


async def build(ctx: AnalysisContext) -> Report:
    database = ctx.data / "state" / "decision.sqlite"

    def read() -> dict[str, Any]:
        with closing(connect(database)) as db:
            return {
                "counts": {
                    t: db.execute(f'SELECT COUNT(*) FROM "{t}"').fetchone()[0]
                    for t in ("snapshots", "contacts", "messages", "responses", "documents")
                },
                "channels": [
                    dict(r)
                    for r in db.execute(
                        "SELECT channel,COUNT(*) AS messages FROM messages GROUP BY channel"
                    )
                ],
                "extraction": [
                    dict(r)
                    for r in db.execute(
                        "SELECT extraction_status,COUNT(*) AS documents FROM documents GROUP BY extraction_status"
                    )
                ],
                "examples": [
                    dict(r)
                    for r in db.execute(
                        "SELECT scope_id,seq,channel,body FROM messages ORDER BY scope_id,seq LIMIT 12"
                    )
                ],
                "no_response": db.execute(
                    "SELECT COUNT(*) FROM snapshots s WHERE NOT EXISTS (SELECT 1 FROM responses r WHERE r.scope_id=s.scope_id)"
                ).fetchone()[0],
            }

    data = ctx.cached("synthetic-bank-visible", {}, read, files=[database])
    report = Report(
        title="Synthetic bank: runtime evidence",
        subtitle="Decision-time coverage, not Planner quality",
    )
    report.metrics(data["counts"])
    report.text(
        "Findings",
        f"Counting snapshots as cases, there are {data['counts']['snapshots']} cases; "
        f"{data['no_response']} have no reviewed read-only bank response. "
        "Contacts are local routing aliases, not authenticated customers. "
        "Entity end state and labels are outside this recipe. PNG contents remain unread; "
        "PDF text extraction is not a visual verification. The response allowlist excludes "
        "command receipts and mixed/unreviewed queries; absence is a gap, not a negative bank finding.",
        collapsed=False,
    )
    report.table("Visible messages by original channel", data["channels"])
    report.table("Attachment extraction coverage", data["extraction"])
    report.table("First case threads: inspect what the collector actually sees", data["examples"])
    return report
