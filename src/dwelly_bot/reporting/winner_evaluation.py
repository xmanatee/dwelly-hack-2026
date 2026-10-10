"""Portable drill-down report over saved decisions and independent judge findings."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from dwelly_bot.reporting.models import Report
from dwelly_bot.reporting.page import render as render_report


def render(bundle: dict[str, Any], output: Path) -> None:
    summary = bundle["summary"]
    report = Report(
        title="Winner · public decision evaluation",
        subtitle=f"{summary['scenarios']} source scenarios · {summary['assigned']} decisions · independent saved-output review",
        receipt=bundle["receipt"],
    )
    report.text(
        "How to read this evaluation",
        "Development examples, not blind assessment. Each input ends before the expected action. No bank operation is executed. Pass/fail/unknown are model judgments, not independently verified banking outcomes. Multiple cuts from a scenario are correlated. A reference may contain facts not yet available; those limitations are reported separately.",
        collapsed=False,
    )
    report.metrics({k: v for k, v in summary.items() if k != "criteria"})
    if review := bundle.get("manual_review"):
        report.text("Manual review · scores are not overwritten", review["scope"], collapsed=False)
        report.table("Confirmed issues and judge limitations", review["findings"])
        report.text("Next experiments", "\n\n".join(review["priorities"]), collapsed=False)
    if diagnostics := bundle.get("diagnostics"):
        report.metrics(diagnostics["cost_by_role_usd"], title="Winner cost by role · USD")
        report.table("Repairs before final output", diagnostics["repairs"])
    report.table(
        "Criteria · all assigned decisions",
        [{"Criterion": k, **v} for k, v in summary["criteria"].items()],
    )
    overview = []
    for row in bundle["cases"]:
        overview.append(
            {
                "Case": row["id"],
                "Scenario": row["scenario"],
                "Execution": row["execution_status"],
                "Judge": row["judge_status"],
                **{f["criterion"]: f["status"] for f in row["judge"]},
            }
        )
    report.table("Decisions", overview)
    for row in bundle["cases"]:
        findings = "\n\n".join(
            f"{f['criterion']}: {f['status']} — {f['reason']}" for f in row["judge"]
        )
        report.text(
            row["id"]
            + " · "
            + row.get("judge_summary", row.get("judge_error", "Execution failed")),
            "JUDGE\n"
            + findings
            + "\n\nCONTEXT\n"
            + row["input"]
            + "\n\nEXPECTED ACTION\n"
            + row["reference"]["action"]
            + "\n\nPLAN\n"
            + json.dumps(row["sources"][0]["plan"], ensure_ascii=False, indent=2)
            + "\n\nANSWER\n"
            + row["answer"]
            + "\n\nREASONING\n"
            + row["public_rationale"],
        )
    render_report(report, output)
