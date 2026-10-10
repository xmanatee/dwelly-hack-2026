"""Build the Case desk dashboard data from saved experiment results.

Offline: reads the two evaluated runs and the reviewed public corpus; makes no model calls.

    uv run python docs/dashboard/build_data.py --output .cache/dashboard
"""

from __future__ import annotations

import argparse
import csv
import gzip
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RUNS = {
    "MiniMax M3": ROOT / "experiments/minimax-baseline/evaluated.json.gz",
    "Sonnet 5.5": ROOT / "experiments/sonnet-vs-minimax-anthropic/evaluated.json.gz",
}
SUMMARY = ROOT / "experiments/sonnet-vs-minimax-anthropic/summary.json"
CORPUS = ROOT / ".cache/datasets/banking-reviewed/original/Banking & Financial Services"
CRITERIA = [
    "evidence_support",
    "next_action",
    "authority",
    "action_truthfulness",
    "customer_response",
]
LABELS = {
    "evidence_support": "Factual grounding",
    "next_action": "Useful next decision",
    "authority": "Authority and uncertainty",
    "action_truthfulness": "Honest action status",
    "customer_response": "Usable customer response",
}


def request_type(number: int) -> str:
    """Topic bands of the public banking set (cases are grouped in tens)."""
    if number <= 10:
        return "Payments & transfers"
    if number <= 20:
        return "Standing orders & Direct Debits"
    if number <= 30:
        return "Cards & access"
    if number <= 40:
        return "Statements, fees & profile"
    return "Business banking"


def case_meta(corpus: Path) -> dict[str, dict[str, str]]:
    meta = {}
    for folder in sorted(p for p in corpus.iterdir() if p.is_dir()):
        index = (folder / "index.md").read_text(encoding="utf-8")
        history = (folder / "history.md").read_text(encoding="utf-8")
        event = re.search(
            r"event 002\n\n- \*\*Channel:\*\* (.*?)\n- \*\*From:\*\* (.*?)\n", history
        )
        role = re.search(r"\*\*Source role:\*\* (.*)", index)
        meta[folder.name] = {
            "title": index.splitlines()[0].split(": ", 1)[1],
            "channel": event.group(1) if event else "",
            "customer": event.group(2) if event else "",
            "role": role.group(1) if role else "",
        }
    return meta


def split_answer(answer: str) -> tuple[str, str]:
    """Separate the drafted customer reply from the operator plan when the answer labels both."""
    reply = re.search(r"^(Customer response(?: \(proposed\))?):\s*", answer, re.M)
    plan = re.search(r"^((?:Proposed )?Operator (?:action )?plan[^:\n]*):\s*", answer, re.M)
    if reply and plan and plan.start() > reply.start():
        return answer[reply.end() : plan.start()].strip(), answer[plan.end() :].strip()
    if reply:
        return answer[reply.end() :].strip(), ""
    return answer.strip(), ""


def write(path: Path, rows: list[dict[str, object]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    print(f"{path}: {len(rows)} rows")


def build(output: Path, corpus: Path) -> None:
    output.mkdir(parents=True, exist_ok=True)
    meta = case_meta(corpus)
    cases: list[dict[str, object]] = []
    answers: list[dict[str, object]] = []
    for model, path in RUNS.items():
        with gzip.open(path) as handle:
            run = json.load(handle)["runs"][0]
        for case in run["cases"]:
            number = case["id"].split("-")[1]
            info = meta[number]
            judge = {item["criterion"]: item for item in case["judge"]}
            checks = {item["id"]: item["status"] for item in case["verifier"]["checks"]}
            metrics, usage = case["metrics"], case["usage"]
            documents = [
                event["arguments"].get("document", "")
                for event in case["tool_events"]
                if event["tool"] == "read_document"
            ]
            flags = sum(judge[c]["status"] != "pass" for c in CRITERIA)
            cases.append(
                {
                    "case": number,
                    "title": info["title"],
                    "type": request_type(int(number)),
                    "channel": info["channel"],
                    "customer": info["customer"],
                    "role": info["role"],
                    "received": case["input"]["decision_time"].replace(" UTC", ""),
                    "model": model,
                    "disposition": case["agent_disposition"],
                    "handling_s": round(metrics["latency_ms"] / 1000, 1),
                    "cost_usd": round(metrics["cost_usd"], 5),
                    "input_tokens": usage["input_tokens"],
                    "output_tokens": usage["output_tokens"],
                    "requests": usage.get("requests"),
                    "documents_read": len(documents),
                    **{c: judge[c]["status"] for c in CRITERIA},
                    "review_flags": flags,
                    "review": "flagged" if flags else "clear",
                    "citation_check": checks.get("citation_observed"),
                }
            )
            reply, plan = split_answer(case["answer"])
            answers.append(
                {
                    "case": number,
                    "model": model,
                    "request": case["input"]["request"],
                    "reply": reply,
                    "plan": plan,
                    "rationale": case["public_rationale"],
                    "evidence": "; ".join(documents),
                    **{f"why_{c}": judge[c]["reason"] for c in CRITERIA},
                }
            )
    write(output / "cases.csv", cases)
    write(output / "answers.csv", answers)

    summary = json.loads(SUMMARY.read_text(encoding="utf-8"))
    criteria = []
    for row in summary["criterion_summary"]:
        model = "MiniMax M3" if "minimax" in row["Run"] else "Sonnet 5.5"
        key = next(k for k, v in LABELS.items() if row["Criterion"].startswith(v))
        criteria.append(
            {
                "model": model,
                "criterion": key,
                "label": LABELS[key],
                "passed": row["Pass"],
                "failed": row["Fail"],
                "unknown": row["Unknown"],
                "assigned": row["Assigned"],
                "pass_rate": round(row["Pass"] / row["Assigned"], 3),
            }
        )
    write(output / "criteria.csv", criteria)

    resources = []
    for key, model in (("minimax", "MiniMax M3"), ("sonnet", "Sonnet 5.5")):
        execution, judge = summary["execution_resources"][key], summary["judge_resources"][key]
        resources.append(
            {
                "model": model,
                "provider": "OpenRouter" if key == "minimax" else "Anthropic (prompt caching)",
                "cases": execution["timed_attempts"],
                "latency_mean_s": round(execution["latency_mean_seconds"], 2),
                "latency_min_s": round(execution["latency_min_seconds"], 2),
                "latency_max_s": round(execution["latency_max_seconds"], 2),
                "cost_usd": round(execution["cost_usd"], 4),
                "cost_per_case_usd": round(execution["cost_mean_usd"], 5),
                "cost_per_1000_usd": round(execution["cost_mean_usd"] * 1000, 2),
                "requests": execution["requests"],
                "input_tokens": execution["input_tokens"],
                "output_tokens": execution["output_tokens"],
                "judge_cost_usd": round(judge["cost_estimate_usd"], 4),
                "judge_requests": judge["requests"],
                "judge_errors": judge["errors"],
                "all_five_pass": summary["all_five_pass"][key],
                "cost_basis": "provider reported"
                if key == "minimax"
                else "configured-rate estimate",
            }
        )
    write(output / "resources.csv", resources)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT / ".cache/dashboard")
    parser.add_argument("--corpus", type=Path, default=CORPUS)
    args = parser.parse_args()
    build(args.output, args.corpus)


if __name__ == "__main__":
    main()
