"""Pinned saved runs, explicit comparisons and an adopted baseline reference."""

from __future__ import annotations

import argparse
import re
import shutil
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from dwelly_bot.adapters.registry import adapter_for
from dwelly_bot.configuration import read_config, read_settings
from dwelly_bot.contracts import RunConfig
from dwelly_bot.evaluation.runner import evaluation_status
from dwelly_bot.evaluation.saved import grade_bundle
from dwelly_bot.experiments.agent import execute
from dwelly_bot.experiments.bundle import comparability, validate
from dwelly_bot.experiments.provenance import (
    dataset_hash,
    evaluator_hash,
    execution_hash,
    grading_profile,
)
from dwelly_bot.paths import ROOT
from dwelly_bot.providers import ledger_path
from dwelly_bot.reporting.html import comparison_rows, render
from dwelly_bot.storage import fingerprint, load_json, save_json


def require_evidence(run: dict[str, Any]) -> None:
    """Keep failed/unstarted cases visible; never treat them as comparable successes."""
    checks = [comparability(run, case, evaluation=False) for case in run["cases"]]
    if not any(check["signature"] for check in checks) or any(
        check["reason"]
        and not (
            case.get("execution_status") in {"error", "not_started", "missing_result"}
            and check["reason"] in {"Case inputs are unconfirmed", "Starting state is unconfirmed"}
            and not case.get("tool_events")
            and not case.get("state_snapshots")
        )
        for case, check in zip(run["cases"], checks, strict=True)
    ):
        raise ValueError("Saved run lacks the provenance required for comparison")


class SavedRun(BaseModel):
    model_config = ConfigDict(extra="forbid")
    path: str
    content_hash: str = Field(pattern=r"^[0-9a-f]{64}$")
    code_revision: str = Field(pattern=r"^[0-9a-f]{64}$")
    config_path: str | None = None

    @classmethod
    def freeze(cls, path: Path, *, config_path: Path | None = None) -> SavedRun:
        path = path.resolve()
        bundle = validate(load_json(path))
        if len(bundle["runs"]) != 1:
            raise ValueError("Select a saved bundle containing exactly one run")
        return cls(
            path=str(path.relative_to(ROOT)) if path.is_relative_to(ROOT) else str(path),
            content_hash=fingerprint(bundle),
            code_revision=bundle["runs"][0]["manifest"]["code_revision"],
            config_path=(
                str(config_path.resolve().relative_to(ROOT))
                if config_path.resolve().is_relative_to(ROOT)
                else str(config_path.resolve())
            )
            if config_path
            else None,
        )

    def load(self) -> dict[str, Any]:
        bundle = validate(load_json(ROOT / self.path))
        if (
            len(bundle["runs"]) != 1
            or fingerprint(bundle) != self.content_hash
            or bundle["runs"][0]["manifest"]["code_revision"] != self.code_revision
        ):
            raise ValueError(f"Saved run changed: {self.path}")
        return bundle

    def require_current(self) -> None:
        run = self.load()["runs"][0]
        manifest = run["manifest"]
        config = RunConfig.model_validate(manifest["resolved_config"])
        if self.config_path is None:
            raise ValueError("Pin the tracked run configuration with --config before adoption")
        if read_config(ROOT / self.config_path) != config:
            raise ValueError("Saved run configuration differs from the tracked configuration")
        changed = manifest.get(
            "execution_changed_during_run", manifest.get("source_changed_during_run")
        )
        current = manifest["execution_hash"] == execution_hash(config.skills)
        if changed or not current:
            raise ValueError("Baseline/result does not represent the current source; run it again")
        dataset = adapter_for(manifest["dataset"]).dataset_root
        if manifest["dataset_hash"] != dataset_hash(dataset):
            raise ValueError("Dataset changed; start a new baseline round")
        require_evidence(run)


class Comparison(BaseModel):
    model_config = ConfigDict(extra="forbid")
    title: str = Field(min_length=1)
    description: str = Field(min_length=1)
    baseline: SavedRun
    candidate: SavedRun
    conclusion: str = ""

    def bundle(self) -> dict[str, Any]:
        before, after = self.baseline.load(), self.candidate.load()
        if regraded := after.get("baseline_evaluation"):
            original_run, new_run = before["runs"][0], regraded["runs"][0]
            # A new evaluation may change assessments, never the underlying execution.
            evaluation_fields = {"verifier", "assessments", "evaluation_contract", "batch_result"}

            def evidence(run: dict[str, Any]) -> list[dict[str, Any]]:
                return [
                    {
                        k: v
                        for k, v in case.items()
                        if k not in evaluation_fields and not k.startswith("judge")
                    }
                    for case in run["cases"]
                ]

            if (
                original_run["id"] != new_run["id"]
                or original_run["manifest"]["code_revision"] != new_run["manifest"]["code_revision"]
                or evidence(original_run) != evidence(new_run)
                or [comparability(original_run, c, evaluation=False) for c in original_run["cases"]]
                != [comparability(new_run, c, evaluation=False) for c in new_run["cases"]]
            ):
                raise ValueError("Baseline re-evaluation changed execution evidence")
            before = regraded
        baseline, candidate = before["runs"][0], after["runs"][0]
        if self.baseline.content_hash == self.candidate.content_hash:
            raise ValueError("Baseline and experiment must be different saved results")
        # Report-local role IDs do not replace the source execution's identity.
        for role, run in [("baseline", baseline), ("candidate", candidate)]:
            run["manifest"]["source_run_id"] = run["id"]
            run["id"] = role
        return {
            "schema_version": 1,
            "title": self.title,
            "notice": "\n".join(
                dict.fromkeys(
                    x
                    for x in [
                        self.description,
                        self.conclusion,
                        before.get("notice"),
                        after.get("notice"),
                    ]
                    if x
                )
            ),
            "attribution": "\n".join(
                dict.fromkeys(x for x in [before.get("attribution"), after.get("attribution")] if x)
            ),
            "runs": [baseline, candidate],
            "comparisons": [{"baseline": baseline["id"], "candidate": candidate["id"]}],
            "experiment": self.model_dump(),
        }


def compare(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(prog="dwelly-bot experiment compare")
    parser.add_argument(
        "spec", type=Path, help="Pinned baseline/candidate and description JSON/TOML"
    )
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    render(Comparison.model_validate(read_settings(args.spec)).bundle(), args.output)
    print(args.output)
    return 0


async def run(argv: list[str]) -> int:
    """Execute only the candidate; the control is immutable, previously saved evidence."""
    parser = argparse.ArgumentParser(prog="dwelly-bot experiment run")
    parser.add_argument("name")
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--description", required=True)
    parser.add_argument(
        "--baseline", type=Path, default=ROOT / "experiments/baseline/reference.json"
    )
    args = parser.parse_args(argv)
    if not re.fullmatch(r"[a-zA-Z0-9_-]+", args.name) or not args.description.strip():
        parser.error("Use a plain experiment name and a nonempty description")
    baseline = SavedRun.model_validate_json(args.baseline.read_text())
    control = baseline.load()["runs"][0]
    manifest = control["manifest"]
    config = read_config(args.config)
    original = RunConfig.model_validate(manifest["resolved_config"])
    adapter = adapter_for(manifest["dataset"])
    # Candidate code/config is expected to differ: never require_current() on the control.
    require_evidence(control)
    if (
        adapter.state_mode != manifest["state_mode"]
        or adapter.state_mode == "shared"
        or config.environment_state_mode != original.environment_state_mode
    ):
        raise ValueError("Candidate must preserve the baseline environment")
    if dataset_hash(adapter.dataset_root) != manifest["dataset_hash"]:
        raise ValueError("Dataset differs from the saved baseline; no agent was run")
    directory = ROOT / "experiments" / args.name
    if (directory / "spec.json").exists() or (directory / "results.json.gz").exists():
        raise ValueError("Use a new experiment name; existing evidence is preserved")
    config_path = directory / "config.json"
    if args.config.resolve() != config_path.resolve():
        save_json(config_path, config.model_dump(mode="json"))
    baseline_evaluation = None
    if evaluator_hash(manifest["dataset"], adapter.dataset_root) != manifest.get(
        "evaluation_profile_hash"
    ):
        # Saved native checks only: no subject, tools or paid judge.
        regraded, _ = await grade_bundle(baseline.load(), adapter.dataset_root, adapter, original)
        grading_profile(regraded, adapter.dataset_root, manifest["dataset"])
        regraded.pop("baseline_evaluation", None)
        baseline_evaluation = regraded
    output = await execute(
        manifest["dataset"],
        config,
        dataset_root=adapter.dataset_root,
        ids=manifest["assigned_case_ids"],
        experiment=args.name,
        artifacts=directory / "artifacts",
    )
    result = load_json(output)
    if baseline_evaluation:
        result["baseline_evaluation"] = baseline_evaluation
    published = directory / "results.json.gz"
    save_json(published, result)
    spec = Comparison(
        title=args.name,
        description=args.description,
        baseline=baseline,
        candidate=SavedRun.freeze(published, config_path=config_path),
    )
    save_json(directory / "spec.json", spec.model_dump())
    html = directory / "comparison.html"
    render(spec.bundle(), html)
    result = spec.candidate.load()
    # Published evidence is portable; incomplete checkpoints remain available for resume.
    if (
        output.is_relative_to(directory / "artifacts")
        and not ledger_path(config).is_relative_to(output.parent.resolve())
        and all(case["execution_status"] == "completed" for case in result["runs"][0]["cases"])
    ):
        shutil.rmtree(output.parent)
    print(f"Candidate results: {published}\nComparison: {html}")
    return int(
        evaluation_status(result)
        or any(case["execution_status"] != "completed" for case in result["runs"][0]["cases"])
    )


def baseline(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(prog="dwelly-bot experiment baseline")
    parser.add_argument("action", choices=["init", "check", "accept"])
    parser.add_argument(
        "input", type=Path, help="Saved result, baseline reference, or comparison spec"
    )
    parser.add_argument("--output", type=Path, help="Adopted baseline reference")
    parser.add_argument("--config", type=Path, help="Tracked run configuration (init only)")
    args = parser.parse_args(argv)
    if args.action == "check":
        SavedRun.model_validate_json(args.input.read_text()).require_current()
        print("Baseline execution matches code, configuration and corpus")
        return 0
    if args.output is None:
        parser.error("--output is required")
    if args.action == "init":
        if args.config is None:
            parser.error("init requires --config")
        adopted = SavedRun.freeze(args.input, config_path=args.config)
        adopted.require_current()
        published = args.output.parent / "results.json.gz"
        if args.input.resolve() != published.resolve():
            save_json(published, adopted.load())
            adopted = SavedRun.freeze(published, config_path=args.config)
        overwrite = False
    else:
        spec = Comparison.model_validate(read_settings(args.input))
        rows = comparison_rows(spec.bundle())
        require_evidence(spec.baseline.load()["runs"][0])
        if any(
            row["change"] == "not comparable"
            and row["fields"]["Reason"]
            not in {"Case inputs are unconfirmed", "Starting state is unconfirmed"}
            for row in rows
        ):
            raise ValueError("Cannot adopt results with incomparable cases")
        if SavedRun.model_validate_json(args.output.read_text()) != spec.baseline:
            raise ValueError("Adopted baseline changed since this experiment; compare again")
        adopted, overwrite = spec.candidate, True
    adopted.require_current()
    save_json(args.output, adopted.model_dump(), overwrite=overwrite)
    print(f"Adopted baseline: {args.output}")
    return 0
