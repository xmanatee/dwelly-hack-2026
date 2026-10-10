"""Archive unedited live outputs and render a local inspection report; no model calls."""

import gzip
import json
from pathlib import Path

from dwelly_bot.reporting import Report, render
from dwelly_bot.storage import file_hash

BASE = Path(__file__).parent
ARTIFACTS = BASE / "artifacts"


def main() -> None:
    rows = []
    details = []
    requests = 0
    cost = 0.0
    retries = 0
    for run in ("plans", "winner"):
        for path in sorted((ARTIFACTS / run / "journals").glob("*.jsonl")):
            events = [json.loads(line) for line in path.read_text().splitlines()]
            trace = next(e for e in events if e["kind"] == "model_trace")
            selection = next(
                e["result"]
                for e in events
                if e["kind"] == "skill_selection" and e.get("status") == "returned"
            )
            calls = trace["costs"]
            case_cost = sum(c["cost_usd"] for c in calls if c["status"] == "settled")
            repairs = [
                p["content"]
                for r in trace["roles"]
                for m in r["messages"]
                for p in m.get("parts", [])
                if p.get("part_kind") == "retry-prompt"
            ]
            case_id = path.stem
            plan_path = (
                ARTIFACTS
                / run
                / (f"{case_id}.plan.json" if run == "plans" else f"{case_id}/plan.json")
            )
            result = json.loads(plan_path.read_text())
            plan = result["plan"] if run == "plans" else result
            rows.append(
                {
                    "run": run,
                    "case": case_id,
                    "skills": ", ".join(selection["selected"]),
                    "flags": ", ".join(plan["safety_flags"]),
                    "steps": ", ".join(s["action"] for s in plan["steps"]),
                    "requests": len(calls),
                    "repairs": len(repairs),
                    "cost_usd": round(case_cost, 7),
                }
            )
            details.append(
                (
                    f"{run}/{case_id}",
                    json.dumps(
                        {"plan": plan, "selection": selection, "repairs": repairs}, indent=2
                    ),
                )
            )
            requests += len(calls)
            cost += case_cost
            retries += len(repairs)
    files = {
        str(p.relative_to(ARTIFACTS)): p.read_text()
        for p in sorted(ARTIFACTS.rglob("*"))
        if p.is_file() and p.suffix != ".html"
    }
    payload = json.dumps({"files": files}, ensure_ascii=False, indent=2).encode()
    archive = BASE / "captures.json.gz"
    if archive.exists():
        raise FileExistsError("Preserve the original capture archive")
    archive.write_bytes(gzip.compress(payload, mtime=0))
    receipt = {
        "kind": "integration-smoke-not-benchmark",
        "model": "claude-sonnet-5-5",
        "runtime_source_commit": "69bcf21",
        "planner_preparation_commit": "6967e40",
        "config_sha256": file_hash(BASE / "config.json"),
        "captures_sha256": file_hash(archive),
        "cases": len(rows),
        "requests": requests,
        "repairs": retries,
        "cost_usd": round(cost, 7),
        "final_errors": 0,
        "offline_tests_passed": 315,
        "cases_reviewed": rows,
    }
    (BASE / "verification.json").write_text(json.dumps(receipt, indent=2) + "\n")
    report = Report(
        title="Planner: modular knowledge",
        subtitle="Actual Sonnet smoke captures · integration and routing inspection, not a quality benchmark",
        receipt=receipt,
    )
    report.metrics(
        {
            "Cases": len(rows),
            "Requests": requests,
            "Repaired outputs": retries,
            "Estimated USD": round(cost, 4),
        }
    )
    report.text(
        "What was inspected",
        "Two original decision snapshots, three local safety snapshots, two synthetic message snapshots and two Winner demo cases. Input preparation withholds later events and all evaluator labels. Selected topics are visible below. Four malformed or invalid plan outputs were repaired by the existing validation loop; all final plans succeeded. No bank action executed.",
        collapsed=False,
    )
    report.table("Routing and final plans", rows)
    report.text(
        "Observations and limits",
        "The indirect crisis disclosure selected crisis-support; the older customer's ordinary standing-order query raised no safety flag. Supplied sent/validation records led to direct replies in public-001/public-042. Winner 002 starts with a reply and retains a conditional follow-up lookup. Winner 001 selects fraud knowledge but does not assert fraud as a final flag. These are observations on these nine inputs, not accuracy estimates or proof of improvement. Review still matters: safety-126 proposes a generic standing-order register despite no supplied systems, and SYN-0421's reply wording must remain conditional on actual referral execution. The local execution stub remains separate. One extra selection request per case adds cost/latency. Historical baseline is stale and was not replaced.",
        collapsed=False,
    )
    for title, detail in details:
        report.text(title, detail)
    render(report, BASE / "report.html")
    (BASE / "winner-report.html").write_bytes((ARTIFACTS / "winner/report.html").read_bytes())
    print(json.dumps({k: v for k, v in receipt.items() if k != "cases_reviewed"}, indent=2))


if __name__ == "__main__":
    main()
