"""Independent, resumable judging of saved Winner output against isolated references."""

from __future__ import annotations

import argparse
import asyncio
from collections import Counter
from pathlib import Path
from typing import Any

from dwelly_bot.evaluation.judge import InvalidReview, review_fields
from dwelly_bot.evaluation.paid import judge_context
from dwelly_bot.resources import text
from dwelly_bot.storage import file_hash, fingerprint, load_json, save_json


def evidence(prepared: Path, predictions: Path) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    manifest = load_json(prepared / "manifest.json")
    saved = load_json(predictions / "predictions.json")
    outputs = {r["case_id"]: r for r in saved["cases"]}
    ids = [row["id"] for row in manifest["cases"]]
    if len(set(ids)) != len(ids) or set(ids) != set(outputs) or len(outputs) != len(saved["cases"]):
        raise ValueError("Evaluation requires exactly all prepared decisions, without duplicates")
    cases, references = [], {}
    for row in manifest["cases"]:
        item = row["id"]
        context_path, action_path = prepared / row["context"], prepared / row["reference"]
        for path, digest in (
            (context_path, row["context_sha256"]),
            (action_path, row["reference_sha256"]),
        ):
            if not path.resolve().is_relative_to(prepared.resolve()) or file_hash(path) != digest:
                raise ValueError(f"Prepared evidence changed: {item}")
        if outputs[item]["input_files"] != {"context.md": row["context_sha256"]}:
            raise ValueError(f"Winner did not use the exact prepared context: {item}")
        folder = predictions / item
        plan = load_json(folder / "plan.json")
        generation = load_json(folder / "generation.json")
        answer, reasoning = (
            (folder / "ANSWER.md").read_text(),
            (folder / "REASONING.md").read_text(),
        )
        if plan != generation["plan"] or any(
            value.strip() != generation["output"][key].strip()
            for key, value in (("answer", answer), ("reasoning", reasoning))
        ):
            raise ValueError(f"Conflicting saved Winner artifacts: {item}")
        context = context_path.read_text()
        expected_context = f"# Supplied case {item}\n\n## context.md\n\n{context}"
        if (
            generation["context"] != expected_context
            or (folder / "context.md").read_text().strip() != expected_context.strip()
        ):
            raise ValueError(f"Winner context does not match preparation: {item}")
        cases.append(
            {
                "id": item,
                "scenario": row["scenario"],
                "input": context,
                "answer": answer,
                "public_rationale": reasoning,
                "sources": [{"plan": plan}],
                "execution_status": "error" if outputs[item]["error"] else "success",
                "error": outputs[item]["error"],
                "winner_metrics": outputs[item],
            }
        )
        references[item] = {
            "action": action_path.read_text(),
            "cutoff": row["decision_time"],
            "role": "Public next-action exemplar; not a unique gold answer",
        }
    return cases, references


def summarize(rows: list[dict[str, Any]]) -> dict[str, Any]:
    counts: dict[str, Counter[str]] = {}
    strict = 0
    scenarios: dict[str, list[bool]] = {}
    for row in rows:
        findings = row.get("judge", [])
        for finding in findings:
            counts.setdefault(finding["criterion"], Counter())[finding["status"]] += 1
        core = [f for f in findings if f["criterion"] != "reference_assessable"]
        passed = len(core) == 5 and all(f["status"] == "pass" for f in core)
        strict += passed
        scenarios.setdefault(row["scenario"], []).append(passed)
    return {
        "assigned": len(rows),
        "scenarios": len(scenarios),
        "execution_errors": sum(r["execution_status"] == "error" for r in rows),
        "judge_errors": sum(r["judge_status"] == "error" for r in rows),
        "all_core_pass": strict,
        "all_decisions_pass_scenarios": sum(all(v) for v in scenarios.values()),
        "criteria": {
            key: {**dict(value), "not_assessed": len(rows) - value.total()}
            for key, value in counts.items()
        },
        "winner_cost_usd": sum(r["winner_metrics"]["cost_usd"] for r in rows),
        "judge_cost_usd": sum(r.get("judge_metrics", {}).get("cost_usd") or 0 for r in rows),
    }


async def evaluate(
    prepared: Path, predictions: Path, config_path: Path, output: Path
) -> dict[str, Any]:
    cases, references = evidence(prepared, predictions)
    rubric = load_json(Path(__file__).parent / "rubrics/winner-reference.json")
    instructions = text("prompts/winner-reference-judge.md")
    async with judge_context(config_path, rubric) as (judge, config):
        # Rebuild instructions on the existing bounded Agent. No model tools are added.
        from pydantic_ai import Agent

        from dwelly_bot.evaluation.judge import JudgeResult

        judge.agent = Agent(
            judge.model,
            output_type=JudgeResult,
            model_settings=judge.settings,
            instructions=instructions,
        )
        judge.agent.instrument = False
        judge.reference_evidence = references
        receipt = {
            "inputs": fingerprint({"cases": cases, "references": references}),
            "judge_config": config.model_dump(mode="json"),
            "rubric": rubric,
            "instructions": instructions,
            "evaluator_sha256": file_hash(Path(__file__)),
            "shared_judge_sha256": file_hash(Path(__file__).with_name("judge.py")),
        }
        output.mkdir(parents=True, exist_ok=True)
        receipt_path = output / "receipt.json"
        if receipt_path.exists():
            if load_json(receipt_path) != receipt:
                raise ValueError("Resume requires identical evidence, evaluator and configuration")
        else:
            if any(output.iterdir()):
                raise ValueError("Nonempty grading directory without a receipt")
            save_json(receipt_path, receipt)
        semaphore = asyncio.Semaphore(config.case_concurrency)

        async def one(case: dict[str, Any]) -> dict[str, Any]:
            path = output / "cases" / f"{case['id']}.json"
            if path.exists():
                return dict(load_json(path))
            async with semaphore:
                row = {
                    **case,
                    "reference": references[case["id"]],
                    "judge": [],
                    "judge_status": "not_run",
                }
                if case["execution_status"] != "error":
                    try:
                        row.update(review_fields(await judge.review(case)))
                    except Exception as error:
                        row.update(
                            judge_status="error", judge_error=f"{type(error).__name__}: {error}"
                        )
                        if isinstance(error, InvalidReview):
                            row["judge_record"] = error.record
                save_json(path, row)
                print(f"judge {case['id']}: {row['judge_status']}", flush=True)
                return row

        rows = await asyncio.gather(*(one(case) for case in cases))
    bundle = {"receipt": receipt, "summary": summarize(rows), "cases": rows}
    result_path = output / "results.json.gz"
    if result_path.exists():
        if load_json(result_path) != bundle:
            raise ValueError("Saved aggregate differs from case receipts")
    else:
        save_json(result_path, bundle)
    from dwelly_bot.reporting.winner_evaluation import render

    render(bundle, output / "report.html")
    return bundle


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--prepared", type=Path, required=True)
    parser.add_argument("--predictions", type=Path, required=True)
    parser.add_argument("--judge-config", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    bundle = asyncio.run(evaluate(args.prepared, args.predictions, args.judge_config, args.output))
    print(bundle["summary"])
    raise SystemExit(
        int(bundle["summary"]["judge_errors"] > 0 or bundle["summary"]["execution_errors"] > 0)
    )


if __name__ == "__main__":
    main()
