"""Grade saved artifacts with Pydantic Evals, then generate our HTML report.

No subject agent or business tools are invoked. A model judge is optional.
"""

# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

import argparse
import copy
import json
from collections.abc import Sequence
from functools import partial
from pathlib import Path
from typing import Any

# This standalone process never configures exporters or session capture.
from pydantic_evals import Case, Dataset
from pydantic_evals.evaluators import EvaluationReason, Evaluator, EvaluatorContext
from pydantic_evals.reporting import EvaluationReportAdapter

from dwelly_bot.contracts import Verification
from dwelly_bot.evaluation.checks import hard_checks
from dwelly_bot.evaluation.judge import ROOT, InvalidReview, LlmJudge, review_fields
from dwelly_bot.experiments.bundle import validate
from dwelly_bot.reporting.html import render
from dwelly_bot.resources import text
from dwelly_bot.storage import fingerprint, load_json, save_json


class SavedChecks(Evaluator[dict[str, Any], dict[str, Any], Any]):
    """Native eval labels over already graded captures, without stateful accumulators."""

    def evaluate(
        self, ctx: EvaluatorContext[dict[str, Any], dict[str, Any], Any]
    ) -> dict[str, Any]:
        verifier = ctx.output["verifier"]
        goal = verifier.get("goal_pass") if verifier["status"] == "available" else None
        return {
            **{
                f"check/{c['id']}": EvaluationReason(value=c["status"], reason=c.get("reason"))
                for c in verifier.get("checks", [])
            },
            "goal": EvaluationReason(
                value=goal if isinstance(goal, bool) else "unknown",
                reason=verifier.get("reason")
                or "Reviewed goal contract and independent observations only.",
            ),
            "verifier_status": verifier["status"],
            "judge_status": ctx.output.get("judge_status", "not_run"),
        }


def evaluation_failed(case: dict[str, Any]) -> bool:
    return case.get("verifier", {}).get("status") == "error" or case.get("judge_status") == "error"


def evaluation_status(bundle: dict[str, Any]) -> int:
    return int(any(evaluation_failed(case) for run in bundle["runs"] for case in run["cases"]))


async def evaluate_bundle(
    bundle: dict[str, Any],
    *,
    judge: LlmJudge | None = None,
    judge_name: str | None = None,
    judge_settings: dict[str, Any] | None = None,
    rubric: dict[str, Any] | None = None,
    concurrency: int = 2,
    preserve_verifier: bool = False,
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    output = validate(copy.deepcopy(bundle))
    rubric = rubric or json.loads((ROOT / "rubrics/default.json").read_text())
    checker_version = fingerprint(
        {
            p.name: p.read_text()
            for p in [
                Path(__file__),
                ROOT / "checks.py",
                ROOT.parent / "contracts.py",
                ROOT.parent / "experiments/bundle.py",
            ]
        }
    )
    native_reports = []
    for run in output["runs"]:
        dataset = Dataset(
            name=run["id"],
            cases=[Case(name=c["id"], inputs=c) for c in run["cases"]],
            evaluators=[SavedChecks()],
        )

        async def grade_saved(artifact: dict[str, Any]) -> dict[str, Any]:
            case: dict[str, Any] = {"judge_status": "not_run", "judge": []}
            try:
                checked = (
                    artifact["verifier"]
                    if preserve_verifier
                    else hard_checks(artifact, artifact.get("evaluation_contract", {}))
                )
                case["verifier"] = Verification.model_validate(checked).model_dump(mode="json")
            except Exception as error:
                case["verifier"] = {"status": "error", "error": str(error), "goal_pass": None}
            if judge:
                try:
                    case.update(review_fields(await judge.review(artifact)))
                except Exception as error:
                    case.update(
                        judge_status="error", judge_error=f"{type(error).__name__}: {error}"
                    )
                    if isinstance(error, InvalidReview):
                        case["judge_record"] = error.record
            return case

        native = await dataset.evaluate(
            grade_saved,
            name=run["id"] + "-saved-grading",
            max_concurrency=concurrency,
            progress=False,
        )
        if native.failures or any(case.evaluator_failures for case in native.cases):
            raise RuntimeError("Pydantic Evals failed to publish saved verification results")
        native_reports.append(json.loads(EvaluationReportAdapter.dump_json(native)))
        rows = {case.name: case.output for case in native.cases}
        if set(rows) != {case["id"] for case in run["cases"]}:
            raise RuntimeError("Pydantic Evals omitted assigned cases")
        for case in run["cases"]:
            for key in {"judge_error", "judge_record", "judge_summary", "judge_metrics"}:
                case.pop(key, None)
            case.update(rows[case["id"]])
        profile = {
            "checker": checker_version,
            "contracts": {c["id"]: c.get("evaluation_contract", {}) for c in run["cases"]},
            "rubric": rubric,
            "instructions": text("prompts/judge.md"),
            "judge_code": fingerprint((ROOT / "judge.py").read_text()),
            "judge_model": judge_name,
            "judge_settings": judge_settings or {},
            "pydantic_evals": "2.54.0",
            "native_verifier_profile": run["manifest"].get("evaluation_profile_hash")
            if preserve_verifier
            else None,
        }
        run["manifest"].update(
            evaluator_version="saved-checks:" + checker_version,
            evaluation_profile_hash=fingerprint(profile),
            evaluation_profile=profile,
        )
    return output, native_reports


async def main(argv: Sequence[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--input", type=Path, required=True)
    p.add_argument(
        "--output", type=Path, required=True, help="New graded bundle; originals are preserved"
    )
    p.add_argument("--html", type=Path, help="Defaults to output path with .html suffix")
    p.add_argument("--rubric", type=Path, default=ROOT / "rubrics/default.json")
    p.add_argument("--concurrency", type=int, default=2)
    p.add_argument("--judge-config", type=Path, help="Opt-in paid judge model/limits TOML or JSON")
    p.add_argument("--dataset", help="Recompute native adapter checks before judging")
    p.add_argument("--dataset-root", type=Path)
    args = p.parse_args(argv)
    html = args.html or args.output.with_suffix(".html")
    if not args.output.name.endswith((".json", ".json.gz")) or html.suffix.lower() not in {
        ".html",
        ".htm",
    }:
        p.error("Use .json or .json.gz for grading output and .html or .htm for the report")
    if any(path.exists() for path in (args.output, html)):
        p.error("Use new output paths for each grading version")
    if args.concurrency < 1:
        p.error("Concurrency must be positive")
    rubric = json.loads(args.rubric.read_text())
    bundle = load_json(args.input)
    if args.dataset:
        from dwelly_bot.adapters.registry import adapter_for
        from dwelly_bot.contracts import RunConfig
        from dwelly_bot.evaluation.saved import verify_bundle
        from dwelly_bot.experiments.provenance import grading_profile

        config = RunConfig.model_validate(bundle["runs"][0]["manifest"]["resolved_config"])
        adapter = adapter_for(args.dataset)
        dataset = args.dataset_root or adapter.dataset_root
        bundle = verify_bundle(bundle, dataset, adapter, config)
        grading_profile(bundle, dataset, args.dataset)
    grade = partial(
        evaluate_bundle,
        bundle,
        rubric=rubric,
        concurrency=args.concurrency,
        preserve_verifier=bool(args.dataset),
    )
    if args.judge_config:
        from dwelly_bot.evaluation.paid import judge_context

        async with judge_context(args.judge_config, rubric) as (judge, config):
            output, _ = await grade(
                judge=judge,
                judge_name=config.model,
                judge_settings=config.model_dump(),
            )
    else:
        output, _ = await grade()
    save_json(args.output, output)
    render(output, html)
    print(f"Saved graded artifacts: {args.output}\nHTML report: {html}")
    return evaluation_status(output)
