"""Run or inspect judge probes; compare with proposed labels without changing them."""

# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

import argparse
import json
from collections.abc import Sequence
from pathlib import Path
from typing import Any

from dwelly_bot.evaluation.judge import InvalidReview, LlmJudge
from dwelly_bot.storage import fingerprint, save_json


def compare(predictions: dict[str, Any], examples: list[dict[str, Any]]) -> dict[str, Any]:
    verdicts = ["pass", "fail", "unknown", "missing"]
    matrix = {expected: {actual: 0 for actual in verdicts} for expected in verdicts[:-1]}
    differences = []
    total = 0
    for example in examples:
        cid = example["case"]["id"]
        prediction = predictions.get(cid, {})
        findings = (
            {f["criterion"]: f["status"] for f in prediction.get("findings", [])}
            if prediction.get("status") == "available"
            else {}
        )
        for criterion, expected in example["expected"].items():
            actual = findings.get(criterion, "missing")
            if actual not in verdicts:
                raise ValueError("Invalid judge verdict")
            total += 1
            matrix[expected][actual] += 1
            if expected != actual:
                differences.append(
                    {"case_id": cid, "criterion": criterion, "expected": expected, "actual": actual}
                )
    return {
        "expected_checks": total,
        "agreement": sum(matrix[v][v] for v in verdicts[:-1]),
        "confusion_counts": matrix,
        "missed_failures_as_pass": matrix["fail"]["pass"],
        "failures_abstained": matrix["fail"]["unknown"],
        "false_accusations": matrix["pass"]["fail"],
        "unknowns_overclaimed": matrix["unknown"]["pass"] + matrix["unknown"]["fail"],
        "missing_predictions": sum(row["missing"] for row in matrix.values()),
        "differences": differences,
    }


async def main(argv: Sequence[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    group = p.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "--list", action="store_true", help="Show proposed probes; no model requests"
    )
    group.add_argument(
        "--predictions", type=Path, help="Compare existing judge predictions; no model requests"
    )
    group.add_argument(
        "--judge-config", type=Path, help="Opt-in paid prediction run under shared budget"
    )
    p.add_argument("--rubric", type=Path)
    p.add_argument(
        "--cases",
        type=Path,
        required=True,
        help="JSON calibration examples; labels stay evaluator-only",
    )
    p.add_argument("--split", choices=["development", "holdout", "all"], default="development")
    p.add_argument("--output", type=Path)
    args = p.parse_args(argv)
    examples = [
        x
        for x in json.loads(args.cases.read_text())
        if args.split == "all" or x["split"] == args.split
    ]
    if not examples:
        p.error("Selected calibration split has no cases")
    if args.list:
        print(
            json.dumps(
                [
                    {
                        "id": x["case"]["id"],
                        "title": x["case"]["title"],
                        "proposed_expected": x["expected"],
                    }
                    for x in examples
                ],
                indent=2,
            )
        )
        return 0
    if not args.output:
        p.error("--output is required for model/prediction comparison")
    if args.output.exists():
        p.error("Use a new output path for each judge calibration version")
    saved: dict[str, Any]
    if args.judge_config:
        from dwelly_bot.evaluation.judge import ROOT
        from dwelly_bot.evaluation.paid import judge_context

        rubric = json.loads((args.rubric or ROOT / "rubrics/default.json").read_text())
        async with judge_context(args.judge_config, rubric) as (judge, config):
            predictions = await evaluate_probes(examples, judge)
        saved = {
            "predictions": predictions,
            "judge_model": config.model,
            "profile_hash": fingerprint(
                {
                    "config": config.model_dump(),
                    "rubric": rubric,
                    "instructions": judge.instructions,
                    "judge_code": (ROOT / "judge.py").read_text(),
                }
            ),
        }
    else:
        saved = json.loads(args.predictions.read_text())
    predictions = saved.get("predictions", saved)
    result: dict[str, Any] = {
        **{key: saved[key] for key in ("judge_model", "profile_hash") if key in saved},
        "scope": "Authored synthetic judge probes; proposed labels require team review, not a production accuracy claim",
        "split": args.split,
        "comparison_profile_hash": fingerprint(
            {"cases": examples, "comparison_code": Path(__file__).read_text()}
        ),
        "comparison": compare(predictions, examples),
        "predictions": predictions,
    }
    if args.predictions:
        result["prediction_source"] = {
            "path": str(args.predictions),
            "content_hash": fingerprint(saved),
            "original_judge_profile_hash": saved.get("profile_hash"),
        }
    save_json(args.output, result)
    print(json.dumps(result["comparison"], indent=2))
    return int(result["comparison"]["missing_predictions"] > 0)


async def evaluate_probes(examples: list[dict[str, Any]], judge: LlmJudge) -> dict[str, Any]:
    """Caller supplies the common budgeted model; expected labels are never sent."""
    predictions: dict[str, Any] = {}
    for example in examples:
        cid = example["case"]["id"]
        try:
            predictions[cid] = await judge.review(example["case"])
        except Exception as exc:
            predictions[cid] = {"status": "error", "error": str(exc)}
            if isinstance(exc, InvalidReview):
                predictions[cid]["record"] = exc.record
    return predictions
