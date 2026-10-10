"""Archive actual execution/evaluation bytes and render saved results, without model calls."""

from __future__ import annotations

import json
import shutil
from collections import Counter
from pathlib import Path

from dwelly_bot.reporting.winner_evaluation import render
from dwelly_bot.storage import file_hash, load_json, save_json

ROOT = Path(__file__).parent


def main() -> None:
    work = ROOT / "artifacts"
    bundle = load_json(work / "graded/results.json.gz")
    costs: Counter[str] = Counter()
    requests: Counter[str] = Counter()
    repairs: Counter[tuple[str, str]] = Counter()
    statuses: Counter[str] = Counter()
    for path in sorted((work / "winner/journals").glob("*.jsonl")):
        for record in map(json.loads, path.read_text().splitlines()):
            roles = {}
            for role in record.get("roles", []):
                for message in role["messages"]:
                    if message.get("kind") == "response":
                        roles[message.get("provider_response_id")] = role["role"]
                    for part in message.get("parts", []):
                        if part.get("part_kind") != "retry-prompt":
                            continue
                        body = str(part.get("content", ""))
                        kind = (
                            "evidence_ids"
                            if "unknown evidence" in body
                            else "completion_wording"
                            if "planned action as done" in body
                            else "schema"
                            if "list_type" in body
                            else "other"
                        )
                        repairs[(role["role"], kind)] += 1
            for call in record.get("costs", []):
                name = roles.get(call.get("response_id"), "unknown")
                requests[name] += 1
                statuses[call["status"]] += 1
                if call["status"] == "settled":
                    costs[name] += call["cost_usd"]
    diagnostics = {
        "cost_by_role_usd": dict(costs),
        "requests_by_role": dict(requests),
        "call_statuses": dict(statuses),
        "repairs": [
            {"role": role, "kind": kind, "count": count} for (role, kind), count in repairs.items()
        ],
        "note": "Planner role includes skill selection. Repair categories are mechanical journal classifications. Prices are configured accounting ceilings, not an invoice.",
    }
    save_json(ROOT / "diagnostics.json", diagnostics)
    files = {}
    for directory in (work / "prepared", work / "winner"):
        for path in sorted(directory.rglob("*")):
            if path.is_file() and path.suffix != ".html":
                files[str(path.relative_to(work))] = path.read_text()
    for name in ("execution-receipt.json", "grading-receipt.json"):
        files[name] = (work / name).read_text()
    save_json(ROOT / "captures.json.gz", {"files": files})
    shutil.copyfile(work / "graded/results.json.gz", ROOT / "results.json.gz")
    bundle["manual_review"] = load_json(ROOT / "review.json")
    bundle["diagnostics"] = diagnostics
    render(bundle, ROOT / "report.html")
    save_json(
        ROOT / "verification.json",
        {
            "execution": load_json(work / "execution-receipt.json"),
            "grading": load_json(work / "grading-receipt.json"),
            "summary": bundle["summary"],
            "captured_files": len(files),
            "captures_sha256": file_hash(ROOT / "captures.json.gz"),
            "results_sha256": file_hash(ROOT / "results.json.gz"),
            "limitations": [
                "Public development population used previously for skills; not a blind holdout.",
                "Decision points within a source scenario are correlated.",
                "Historical next actions are examples, not independently annotated unique ground truth.",
                "Sonnet subject and Opus judge are different models from the same vendor family.",
                "No real bank tools or effects; proposed actions only.",
                "No comparison or baseline adoption is implied by this control run.",
            ],
        },
    )
    print(ROOT / "report.html")


if __name__ == "__main__":
    main()
