"""Reproducible lexical topic inventory of histories or decision-time messages, no labels."""

import re
from contextlib import closing
from typing import Any

from dwelly_bot.adapters.synthetic_banking.sources import connect
from dwelly_bot.analysis import AnalysisContext, Report

# Deliberately transparent screening terms, NOT runtime retrieval or verified labels.
TOPICS = {
    "payments": r"transfer|incoming payment|refund|recipient|duplicate",
    "scheduled-payments": r"standing order|standing-order|direct debit|future payment",
    "cards-access": r"card|device|sign.in|PIN\b|phone number|address|profile|clos.{0,8}account",
    "business-authority": r"company|payroll|batch|signatory|employee|acquiring|supplier",
    "fraud-takeover": r"scam|fraud|safe account|release fee|phish|unrecognised|unauthorised",
    "financial-abuse": r"abuse|coerc|controlling|partner.{0,40}(monitor|check)|discreet",
    "vulnerability-support": r"hardship|gambling|debt|payday|breathing space|interpreter|human|job loss",
    "bereavement-authority": r"bereave|funeral|died|death|deceased|attorney",
    "crisis-support": r"suicid|kill myself|end my life|hurt myself|self.harm",
    "complaints-rights": r"complain|redress|ombudsman|fee|chargeback",
    "privacy-documents": r"statement|export|confirmation|privacy|personal data|delete|accountant",
}


async def build(ctx: AnalysisContext) -> Report:
    database = ctx.data / "state" / "decision.sqlite"
    histories = sorted(ctx.data.glob("*/history.md"))
    files = [database] if database.is_file() else histories
    if not files:
        raise ValueError("Expected state/decision.sqlite or folders containing history.md")

    def read() -> list[dict[str, Any]]:
        if database.is_file():
            grouped: dict[str, list[str]] = {}
            with closing(connect(database)) as db:
                for row in db.execute("SELECT scope_id,body FROM messages ORDER BY scope_id,seq"):
                    grouped.setdefault(row["scope_id"], []).append(row["body"])
            return [{"id": k, "text": "\n".join(v)} for k, v in grouped.items()]
        return [{"id": p.parent.name, "text": p.read_text()} for p in histories]

    cases = ctx.cached("planner-topic-screen", {}, read, files=files)
    rows = []
    covered: set[str] = set()
    for topic, pattern in TOPICS.items():
        matches = [c for c in cases if re.search(pattern, c["text"], re.I)]
        covered.update(c["id"] for c in matches)
        rows.append(
            {
                "topic": topic,
                "matching_cases": len(matches),
                "pattern": pattern,
                "examples": ", ".join(c["id"] for c in matches[:5]),
            }
        )
    report = Report(title="Planner knowledge: source topic screen")
    report.metrics({"Cases": len(cases), "Cases with lexical matches": len(covered)})
    report.text(
        "Method and limits",
        "Unit: one case. Multi-label regex screening; matches are navigation hints, not verified "
        "topic labels, risk flags or measured skill coverage. Absence of a match does not prove "
        "absence of a topic. Folder inputs use full public/test histories retrospectively; "
        "SQLite uses decision-time messages only. Attachments, private labels and final entity "
        "state are never opened. Do not feed this report or future history into runtime retrieval.",
        collapsed=False,
    )
    report.table("Topics to inspect", rows)
    report.table(
        "Opening text for manual review",
        [{"id": c["id"], "opening": c["text"][:1200]} for c in cases],
        collapsed=True,
    )
    return report
