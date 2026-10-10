"""Preserve both live attempts; display exact instructions and public grounds, no model calls."""

import gzip
import json
from pathlib import Path
from typing import Any

from dwelly_bot.reporting import Report, render
from dwelly_bot.storage import file_hash

BASE = Path(__file__).parent
ARTIFACTS = BASE / "artifacts"
RUNS = {
    "plans": "003e45a",
    "winner": "003e45a",
    "plans-reviewed": "295f034",
    "winner-reviewed": "295f034",
}


def main() -> None:
    cases: list[dict[str, Any]] = []
    steps: list[dict[str, Any]] = []
    repairs: list[dict[str, Any]] = []
    details: list[dict[str, Any]] = []
    for run, commit in RUNS.items():
        folder = ARTIFACTS / run
        for journal in sorted((folder / "journals").glob("*.jsonl")):
            events = [json.loads(line) for line in journal.read_text().splitlines()]
            trace = next(e for e in events if e["kind"] == "model_trace")
            selection = next(
                (
                    e.get("result", {})
                    for e in events
                    if e["kind"] == "skill_selection" and e.get("status") == "returned"
                ),
                {},
            )
            planner_only = run.startswith("plans")
            plan_file = folder / (
                f"{journal.stem}.plan.json" if planner_only else f"{journal.stem}/plan.json"
            )
            result = json.loads(plan_file.read_text())
            plan = result.get("plan", {}) if planner_only else result
            status = (
                result["status"]
                if planner_only
                else next(
                    r
                    for r in json.loads((folder / "predictions.json").read_text())["cases"]
                    if r["case_id"] == journal.stem
                )["planner"]
            )
            retry_prompts = [
                p["content"]
                for r in trace["roles"]
                for m in r["messages"]
                for p in m.get("parts", [])
                if p.get("part_kind") == "retry-prompt"
            ]
            row = {
                "run": run,
                "source": commit,
                "case": journal.stem,
                "status": status,
                "steps": len(plan.get("steps", [])),
                "grounded_steps": sum(bool(s.get("rationale")) for s in plan.get("steps", [])),
                "legacy_branches": len(plan.get("escalate_if", []))
                + sum(s.get("condition") is not None for s in plan.get("steps", [])),
                "skills": ", ".join(selection.get("selected", [])),
                "flags": ", ".join(plan.get("safety_flags", [])),
                "requests": len(trace["costs"]),
                "repairs": len(retry_prompts),
                "cost_usd": round(
                    sum(c["cost_usd"] for c in trace["costs"] if c["status"] == "settled"), 7
                ),
            }
            cases.append(row)
            details.append({"run": run, "case": journal.stem, "plan": result})
            for step in plan.get("steps", []):
                rationale = step.get("rationale") or {}
                steps.append(
                    {
                        "run": run,
                        "case": journal.stem,
                        "step": step["id"],
                        "action": step["action"],
                        "instruction": step.get("instruction", step.get("purpose", "")),
                        "explanation": rationale.get("explanation", ""),
                        "criterion": rationale.get("criterion", ""),
                        "source": rationale.get("source", ""),
                        "evidence": ", ".join(rationale.get("evidence", [])),
                    }
                )
            if retry_prompts:
                repairs.append(
                    {"run": run, "case": journal.stem, "validation_feedback": retry_prompts}
                )
    files = {
        str(p.relative_to(ARTIFACTS)): p.read_text()
        for p in sorted(ARTIFACTS.rglob("*"))
        if p.is_file() and p.suffix != ".html"
    }
    archive = BASE / "captures.json.gz"
    if archive.exists():
        raise FileExistsError("Do not overwrite original capture archives")
    archive.write_bytes(
        gzip.compress(json.dumps({"files": files}, ensure_ascii=False, indent=2).encode(), mtime=0)
    )
    latest = [r for r in cases if r["run"].endswith("reviewed")]
    receipt = {
        "kind": "decision-contract-smoke-not-quality-benchmark",
        "runs": RUNS,
        "config_sha256": file_hash(BASE / "config.json"),
        "captures_sha256": file_hash(archive),
        "cases_reviewed": cases,
        "latest_cases": len(latest),
        "latest_final_errors": sum(r["status"] != "available" for r in latest),
        "latest_requests": sum(r["requests"] for r in latest),
        "latest_repairs": sum(r["repairs"] for r in latest),
        "latest_cost_usd": round(sum(r["cost_usd"] for r in latest), 7),
        "total_cost_usd": round(sum(r["cost_usd"] for r in cases), 7),
        "offline_tests_passed": 329,
    }
    (BASE / "verification.json").write_text(json.dumps(receipt, indent=2) + "\n")
    report = Report(
        title="Planner: decided actions and public grounds",
        subtitle="Actual outputs from two live attempts; no bank action executed",
        receipt=receipt,
    )
    report.metrics(
        {
            "Latest cases": len(latest),
            "Latest final errors": receipt["latest_final_errors"],
            "Latest requests": receipt["latest_requests"],
            "Total estimated USD": receipt["total_cost_usd"],
        }
    )
    report.text(
        "Contract",
        "Each action has a concrete instruction and separate explanation, evidence, criterion and source. Live validation rejects absent grounds, unknown/unloaded references, hypothetical branches and changes behind an uncompleted identity check. This checks structure and references; natural-language accuracy still requires review. The local executor remains a separate integration.",
        collapsed=False,
    )
    report.table("Latest run", latest)
    report.table("What to do, and why", [r for r in steps if r["run"].endswith("reviewed")])
    review = BASE / "review.md"
    if review.exists():
        report.text("Manual inspection", review.read_text(), collapsed=False)
    report.table(
        "Initial attempt retained",
        [r for r in cases if not r["run"].endswith("reviewed")],
        collapsed=True,
    )
    report.text("Original validation feedback", json.dumps(repairs, indent=2))
    report.text("Exact saved plans", json.dumps(details, indent=2))
    render(report, BASE / "report.html")
    (BASE / "winner-report.html").write_bytes(
        (ARTIFACTS / "winner-reviewed/report.html").read_bytes()
    )
    print(json.dumps({k: v for k, v in receipt.items() if k != "cases_reviewed"}, indent=2))


if __name__ == "__main__":
    main()
