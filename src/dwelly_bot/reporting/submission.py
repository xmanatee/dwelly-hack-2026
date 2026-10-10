"""Faithful ANSWERS export from one saved run; never repair failed agent output."""

from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path
from typing import Any

from dwelly_bot.experiments.bundle import validate, verified_outcome
from dwelly_bot.storage import fingerprint, load_json, save_json


def check_destination(directory: Path) -> None:
    if directory.exists() and (
        not directory.is_dir() or any(path.name != "README.md" for path in directory.iterdir())
    ):
        raise ValueError("Export into an empty directory; existing answers are never overwritten")


def export(bundle: dict[str, Any], directory: Path, run_id: str | None = None) -> None:
    bundle = validate(copy.deepcopy(bundle))
    runs = [r for r in bundle["runs"] if run_id is None or r["id"] == run_id]
    if len(runs) != 1:
        raise ValueError("Select exactly one saved run for ANSWERS export")
    check_destination(directory)
    run = runs[0]
    directory.mkdir(parents=True, exist_ok=True)
    mapping = []
    for index, case in enumerate(run["cases"], 1):
        target = directory / str(index)
        target.mkdir()
        answer = case.get("answer")
        if answer is None:
            answer = "Processing did not produce a final answer; this case requires human review."
        if not isinstance(answer, str):
            answer = json.dumps(answer, ensure_ascii=False, indent=2)
        (target / "ANSWER.md").write_text(answer + "\n")
        reason = [
            f"- Case: `{case['id']}`",
            f"- Execution: `{case.get('execution_status', 'unknown')}`",
            f"- Disposition: `{case.get('agent_disposition', 'unknown')}`",
            f"- Verified goal: `{verified_outcome(case)}`",
            "- Explanation: "
            + str(case.get("public_rationale") or "No public rationale was captured."),
        ]
        if case.get("stop_reason"):
            reason.append("- Run stop: " + str(case["stop_reason"]))
        for event in case.get("tool_events", []):
            reason.append(
                f"- Action `{event.get('id', '?')}` / `{event.get('tool', '?')}`: `{event.get('status', 'unknown')}`"
            )
        reason.append(
            "- Evidence: [trace.json](trace.json); generated from saved observations, without replay."
        )
        (target / "REASONING.md").write_text("\n".join(reason) + "\n")
        # Role transcripts include internal prompts and hidden thinking;
        # keep those local. Export observed public inputs/actions/states, not model internals.
        trace = {
            k: copy.deepcopy(v)
            for k, v in case.items()
            if k
            in {
                "id",
                "input",
                "input_hash",
                "answer",
                "public_rationale",
                "agent_disposition",
                "execution_status",
                "stop_reason",
                "tool_events",
                "state_snapshots",
                "initial_state_hash",
                "final_state_hash",
                "verifier",
                "metrics",
                "sources",
            }
        }
        for event in trace.get("tool_events", []):
            if isinstance(event.get("error"), dict):
                event["error"] = {"type": event["error"].get("type", "Error")}
        save_json(target / "trace.json", trace)
        mapping.append(
            {"directory": str(index), "case_id": case["id"], "saved_case_hash": fingerprint(case)}
        )
    save_json(
        directory / "manifest.json",
        {"run_id": run["id"], "run_manifest": run["manifest"], "cases": mapping},
    )


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(prog="dwelly-bot export")
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--run-id")
    args = parser.parse_args(argv)
    export(load_json(args.input), args.output, args.run_id)
    print(args.output)
    return 0
