"""Join authorized isolated-world continuations without erasing earlier attempts."""

from __future__ import annotations

import copy
from pathlib import Path
from typing import Any

from dwelly_bot.experiments.bundle import validate
from dwelly_bot.storage import fingerprint, load_json


def behavior(config: dict[str, Any]) -> dict[str, Any]:
    """Spending allowances may change; model and case limits may not."""
    return {
        key: behavior(value) if isinstance(value, dict) else value
        for key, value in config.items()
        if key not in {"account_budget_usd", "total_budget_usd"}
    }


def combine(paths: list[Path]) -> dict[str, Any]:
    bundles = [validate(load_json(path)) for path in paths]
    if not bundles or any(len(bundle["runs"]) != 1 for bundle in bundles):
        raise ValueError("Provide one original run followed by its continuation runs")
    result = copy.deepcopy(bundles[0])
    target = result["runs"][0]
    manifest = target["manifest"]
    cases = {case["id"]: case for case in target["cases"]}
    config = behavior(manifest["resolved_config"])
    runtime = None
    receipts = []
    for bundle in bundles:
        run = bundle["runs"][0]
        metadata = run["manifest"]
        signature = metadata["execution_hash"]
        if (
            metadata["state_mode"] not in {"static", "isolated"}
            or metadata.get("execution_changed_during_run")
            or behavior(metadata["resolved_config"]) != config
            or any(
                metadata[key] != manifest[key]
                for key in ("dataset_hash", "environment_version", "evaluation_profile_hash")
            )
            or (runtime is not None and signature != runtime)
        ):
            raise ValueError("Continuation must preserve isolated runtime, data and evaluation")
        runtime = signature
        receipts.append({"manifest": metadata, "bundle_hash": fingerprint(bundle)})
        for case in run["cases"]:
            if case["id"] not in cases:
                raise ValueError("Continuation added an unassigned case")
            case = copy.deepcopy(case)
            case["attempt_run_id"] = run["id"]
            previous = cases[case["id"]]
            if len(receipts) > 1:
                if (
                    case.get("input") != previous.get("input")
                    or (
                        previous.get("initial_state_hash")
                        and case.get("initial_state_hash")
                        and case["initial_state_hash"] != previous["initial_state_hash"]
                    )
                    or not (
                        previous["execution_status"] in {"not_started", "cancelled"}
                        or str(previous.get("error", "")).startswith("BudgetExceeded:")
                    )
                ):
                    raise ValueError(
                        "Only budget-blocked/interrupted cases may be retried from the same inputs/state"
                    )
                case["previous_attempts"] = [*previous.pop("previous_attempts", []), previous]
            cases[case["id"]] = case
    latest = receipts[-1]["manifest"]
    target["manifest"] = {
        **latest,
        "assigned_case_ids": manifest["assigned_case_ids"],
        "selected_cases": len(cases),
        "continuations": receipts,
    }
    target["id"] = bundles[-1]["runs"][0]["id"] + "-combined"
    target["cases"] = [cases[cid] for cid in manifest["assigned_case_ids"]]
    result["notice"] = (
        "Latest attempts after authorized budget continuation; earlier attempts and their costs are retained. Single-run evidence, not a controlled model ranking."
    )
    return result


def main(argv: list[str]) -> int:
    import argparse

    from dwelly_bot.storage import save_json

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("inputs", nargs="+", type=Path, help="Original run, then continuations")
    parser.add_argument("--output", required=True, type=Path, help="New evidence directory")
    args = parser.parse_args(argv)
    bundle = combine(args.inputs)
    args.output.mkdir(parents=True, exist_ok=False)
    save_json(args.output / "results.json.gz", bundle)
    print(args.output / "results.json.gz")
    return 0
