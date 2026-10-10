"""Render saved run artifacts as one offline, read-only HTML file."""

# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

import argparse
import copy
from collections.abc import Sequence
from pathlib import Path
from typing import Any

from dwelly_bot.configuration import read_settings
from dwelly_bot.evaluation.checks import pointer
from dwelly_bot.experiments.bundle import comparability, validate, verified_outcome
from dwelly_bot.reporting.evaluations import evaluation_rows, judge_summary
from dwelly_bot.reporting.models import Report, ReportProfile
from dwelly_bot.reporting.page import render as render_report
from dwelly_bot.reporting.resources import summarize as resources
from dwelly_bot.storage import fingerprint, load_json

RESOURCE_FIELDS = {
    "Timed": "timed_attempts",
    "Cost-known attempts": "costed_attempts",
    "Mean case time (s)": "latency_mean_seconds",
    "Min case time (s)": "latency_min_seconds",
    "Max case time (s)": "latency_max_seconds",
    "Cumulative case time (s)": "cumulative_case_seconds",
    "Execution cost (USD)": "cost_usd",
    "Mean processing cost (USD)": "cost_mean_usd",
    "Known cost (USD)": "known_cost_usd",
    "Unconfirmed exposure (USD)": "unconfirmed_exposure_usd",
    "LLM requests": "requests",
    "Input tokens": "input_tokens",
    "Output tokens": "output_tokens",
}


def comparison_rows(bundle: dict[str, Any]) -> list[dict[str, Any]]:
    """Admit explicit pairs and compare independently observed case outcomes."""
    saved = bundle["runs"]
    pairs = bundle.get("comparisons", [])
    if len(saved) == 1:
        if pairs:
            raise ValueError("A comparison report requires exactly two runs")
        return []
    if len(saved) != 2:
        raise ValueError(
            "A comparison report requires exactly two runs; select one baseline and one candidate"
        )
    if len(pairs) != 1 or {pairs[0].get("baseline"), pairs[0].get("candidate")} != {
        r["id"] for r in saved
    }:
        raise ValueError("Declare exactly one baseline/candidate pair for the two runs")
    datasets = {r["manifest"].get("dataset") for r in saved} - {None}
    if len(datasets) > 1:
        raise ValueError("Comparison requires the same dataset")
    runs = {run["id"]: run for run in saved}
    rows = []
    pair = pairs[0]
    baseline, candidate = runs[pair["baseline"]], runs[pair["candidate"]]
    corpus = baseline["manifest"].get("dataset_hash")
    if not corpus or corpus != candidate["manifest"].get("dataset_hash"):
        raise ValueError("Comparison requires the same pinned benchmark corpus")
    before = {case["id"]: case for case in baseline["cases"]}
    after = {case["id"]: case for case in candidate["cases"]}
    if before.keys() != after.keys():
        raise ValueError("Comparison requires the same assigned cases")
    for cid, old in before.items():
        new = after[cid]
        left, right = comparability(baseline, old), comparability(candidate, new)
        old_goal, new_goal = verified_outcome(old), verified_outcome(new)
        comparable = left["signature"] is not None and left["signature"] == right["signature"]
        change = (
            "not comparable"
            if not comparable
            else "unknown"
            if old_goal is None or new_goal is None
            else "unchanged"
            if old_goal == new_goal
            else "improved"
            if new_goal
            else "regressed"
        )
        rows.append(
            {
                "id": fingerprint([baseline["id"], candidate["id"], cid]),
                "title": old.get("title", cid),
                "change": change,
                "fields": {
                    "Case": cid,
                    "Change": change,
                    "Baseline": old_goal,
                    "Experiment": new_goal,
                    "Reason": left["reason"]
                    or right["reason"]
                    or (
                        "Same comparison fingerprints"
                        if comparable
                        else "Comparison fingerprints differ"
                    ),
                },
                "comparison": {
                    "baseline": fingerprint([baseline["id"], cid]),
                    "candidate": fingerprint([candidate["id"], cid]),
                },
            }
        )
    return rows


def outcomes(run: dict[str, Any]) -> dict[str, Any]:
    """Saved outcomes and execution completion, with every assigned case counted."""
    goals = [verified_outcome(case) for case in run["cases"]]
    return {
        "run": run.get("label", run["id"]),
        "assigned": len(goals),
        "verified": goals.count(True),
        "unmet": goals.count(False),
        "unknown": goals.count(None),
        "critical_flags": sum(
            verified_outcome(case, "critical_failure") is True for case in run["cases"]
        ),
        "execution_errors": sum(case["execution_status"] != "completed" for case in run["cases"]),
    }


def build(bundle: dict[str, Any], profile: ReportProfile | None = None) -> Report:
    """Display saved facts only; the same blocks also serve dataset analysis recipes."""
    bundle = validate(copy.deepcopy(bundle))
    profile = profile or ReportProfile()
    report = Report(title=profile.title or bundle.get("title", "Saved runs"))
    summaries, records, resource_rows = [], [], []
    changes = comparison_rows(bundle)
    roles = {
        pair[role]: role
        for pair in bundle.get("comparisons", [])
        for role in ("baseline", "candidate")
    }
    for run in bundle["runs"]:
        config = run["manifest"].get("resolved_config", {})
        stats = resources(run["cases"])
        resource_rows.append(
            {
                "Run": run.get("label", run["id"]),
                "Role": roles.get(run["id"]),
                "Benchmark": run["manifest"].get("dataset"),
                "Git commit": run["manifest"].get("git_commit"),
                "Uncommitted changes": run["manifest"].get("git_dirty"),
                "Model": run["manifest"].get("model"),
                "Provider": config.get("provider"),
                "Effort": config.get("reasoning_effort"),
                "Parallel cases": config.get("case_concurrency"),
                "Max output tokens": config.get("max_tokens"),
                "Assigned": len(run["cases"]),
                **{label: stats[key] for label, key in RESOURCE_FIELDS.items()},
            }
        )
        summaries.append(outcomes(run))
        for case in run["cases"]:
            goal = verified_outcome(case)
            outcome = "pass" if goal is True else "fail" if goal is False else "unknown"
            comparison = comparability(run, case)
            records.append(
                {
                    "id": fingerprint([run["id"], case["id"]]),
                    "run_id": run["id"],
                    "title": f"{run.get('label', run['id'])} · {case.get('title', case['id'])}",
                    "goal_status": outcome,
                    "fields": {
                        **{label: pointer(case, path)[1] for label, path in profile.fields.items()},
                        "Case": case["id"],
                        "Execution": case["execution_status"],
                        "Disposition": case.get("agent_disposition"),
                        "Verified outcome": outcome,
                        "Critical failure": verified_outcome(case, "critical_failure"),
                        "Execution error": case.get("error"),
                        "Judge status": case.get("judge_status"),
                        "Verification status": case.get("verifier", {}).get("status"),
                        "Evaluation error": case.get("verifier", {}).get("error")
                        or (
                            case.get("verifier", {}).get("reason")
                            if case.get("verifier", {}).get("status") == "error"
                            else None
                        )
                        or case.get("judge_error"),
                    },
                    "comparability": comparison,
                    "raw_capture": case,
                }
            )
    report.subtitle = bundle.get("notice", "")
    if not changes:
        report.metrics({"Assigned attempts": sum(row["assigned"] for row in summaries)})
    if judged := judge_summary(bundle):
        report.table(
            "Model review by criterion",
            judged,
            note="Model judgments over saved evidence; these are not verified operational outcomes. See evaluation details for reasons and paired cases.",
        )
    if changes:
        report.records("Case comparison", changes)
    report.records("Cases", records)
    report.table("Run outcomes", summaries)
    report.records("Evaluation details", evaluation_rows(bundle))
    total_resources = resources([case for run in bundle["runs"] for case in run["cases"]])
    report.table(
        "Resource totals",
        [
            {"Metric": label, "Value": total_resources[key]}
            for label, key in RESOURCE_FIELDS.items()
        ],
    )
    report.table("Run resources", resource_rows)
    report.receipt = {
        "profile": profile.model_dump(),
        "attribution": bundle.get("attribution"),
        "experiment": bundle.get("experiment"),
        "comparisons": bundle.get("comparisons", []),
        "runs": [{"id": run["id"], "manifest": run["manifest"]} for run in bundle["runs"]],
        "execution_resources": total_resources,
    }
    return report


def render(bundle: dict[str, Any], output: Path, profile: ReportProfile | None = None) -> None:
    render_report(build(bundle, profile), output)


def main(argv: Sequence[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--input",
        type=Path,
        required=True,
        help="One saved run, or a saved bundle with one explicit baseline/candidate pair",
    )
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--profile", type=Path, help="Display title/fields TOML or JSON")
    args = parser.parse_args(argv)
    bundle = validate(load_json(args.input))
    profile = ReportProfile.model_validate(read_settings(args.profile)) if args.profile else None
    render(bundle, args.output, profile)
    print(f"Saved offline report: {args.output} ({args.output.stat().st_size:,} bytes)")
