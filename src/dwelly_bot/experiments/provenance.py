"""Immutable source receipts, including shared read-only application dependencies."""

from __future__ import annotations

import ast
import hashlib
import inspect
import json
import subprocess
import tomllib
from pathlib import Path
from typing import Any

from dwelly_bot.data import BOOTSTRAP_FILES
from dwelly_bot.paths import ROOT
from dwelly_bot.storage import file_hash, fingerprint

SOURCE_SUFFIXES = {".py", ".md", ".hbs", ".html", ".json", ".css", ".js", ".typed"}

# Offline discovery prompts share package resources with the acting agent.
ANALYSIS_PROMPTS = {
    "discovery-screen.md",
    "unflagged-audit.md",
    "cross-record-conflicts.md",
    "observed-procedures.md",
    "fact-extraction.md",
    "intent-taxonomy.md",
    "taxonomy-assignments.md",
    "procedure-draft.md",
}


def semantic_hash(path: Path) -> str:
    """Ignore Python comments/formatting; preserve docstrings used as tool instructions."""
    if path.suffix == ".py":
        return fingerprint(ast.dump(ast.parse(path.read_text()), include_attributes=False))
    return file_hash(path)


def execution_hash(extra: list[str] | None = None) -> str:
    """Fingerprint runtime semantics without copying source code."""
    files = {name: path.read_bytes() for name, path in source_files(extra).items()}
    payload = {
        name: fingerprint(ast.dump(ast.parse(data), include_attributes=False))
        if name.endswith(".py")
        else hashlib.sha256(data).hexdigest()
        for name, data in files.items()
        if (name.startswith(("src/dwelly_bot/", "trusted-skills/")) or name == "uv.lock")
        and not name.startswith(
            (
                "src/dwelly_bot/analysis/",
                "src/dwelly_bot/reporting/",
                "src/dwelly_bot/evaluation/",
            )
        )
        and name
        not in {
            "src/dwelly_bot/prompts/judge.md",
            "src/dwelly_bot/experiments/comparison.py",
            "src/dwelly_bot/experiments/provenance.py",
            "src/dwelly_bot/experiments/cli.py",
        }
        and not (name.startswith("src/dwelly_bot/prompts/") and Path(name).name in ANALYSIS_PROMPTS)
    }
    project = tomllib.loads(files["pyproject.toml"].decode())["project"]
    payload["runtime_requirements"] = fingerprint(
        {key: project.get(key) for key in ("requires-python", "dependencies")}
    )
    return fingerprint({"version": 3, "files": payload})


def dataset_hash(directory: Path) -> str:
    """Verify pinned files before execution; a changed corpus cannot reuse an old receipt."""
    root = directory.resolve()
    receipt = json.loads((root / "source.json").read_text())
    actual = {}
    for record in receipt["files"]:
        path = (root / record["path"]).resolve()
        if not path.is_relative_to(root):
            raise ValueError("Dataset file escapes its root")
        digest = file_hash(path)
        if digest != record["sha256"] or path.stat().st_size != record["bytes"]:
            raise ValueError(f"Dataset integrity mismatch: {record['path']}")
        actual[record["path"]] = digest
    inventory = {str(path.relative_to(root)) for path in root.rglob("*") if path.is_file()}
    unpinned = inventory - set(actual) - BOOTSTRAP_FILES
    if unpinned:
        raise ValueError("Dataset contains unpinned files: " + ", ".join(sorted(unpinned)))
    return hashlib.sha256(json.dumps(actual, sort_keys=True).encode()).hexdigest()


def evaluator_hash(name: str, directory: Path) -> str:
    """Model settings/skills are experiment variants, not independent verifier changes."""
    from dwelly_bot.adapters.registry import adapter_for

    adapter_source = Path(inspect.getfile(type(adapter_for(name))))
    files = [
        ROOT / "src/dwelly_bot/evaluation/saved.py",
        ROOT / "src/dwelly_bot/evaluation/runner.py",
        ROOT / "src/dwelly_bot/evaluation/checks.py",
        ROOT / "src/dwelly_bot/experiments/bundle.py",
        ROOT / "src/dwelly_bot/contracts.py",
        adapter_source,
    ]
    payload = {
        str(p.relative_to(ROOT)) if p.is_relative_to(ROOT) else p.name: semantic_hash(p)
        for p in files
    }
    payload["verified_dataset"] = dataset_hash(directory)
    return hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()


def source_files(extra: list[str] | None = None) -> dict[str, Path]:
    files = {
        str(p.relative_to(ROOT)): p
        for p in (ROOT / "src/dwelly_bot").rglob("*")
        if p.is_file() and p.suffix in SOURCE_SUFFIXES
    }
    files.update(
        {
            str(p.relative_to(ROOT)): p
            for p in (ROOT / "configs").rglob("*")
            if p.is_file() and p.suffix in {".toml", ".json"}
        }
    )
    for name in ["pyproject.toml", "uv.lock", "LICENSE"]:
        files[name] = ROOT / name
    for value in extra or []:
        path = (ROOT / value).resolve()
        name = "trusted-skills/" + hashlib.sha256(value.encode()).hexdigest()[:12] + ".md"
        files[name] = path
    return files


def source_hash(extra: list[str] | None = None) -> str:
    manifest = {name: file_hash(p) for name, p in source_files(extra).items()}
    return hashlib.sha256(json.dumps(manifest, sort_keys=True).encode()).hexdigest()


def git_receipt() -> dict[str, Any]:
    """Git owns source history; dirty runs are explicitly not reproducible from HEAD alone."""

    def git(*args: str) -> str:
        return subprocess.check_output(["git", *args], cwd=ROOT, text=True).strip()

    return {"git_commit": git("rev-parse", "HEAD"), "git_dirty": bool(git("status", "--porcelain"))}


def grading_profile(bundle: dict[str, Any], dataset: Path, name: str) -> None:
    for run in bundle["runs"]:
        run["manifest"]["evaluator_version"] = "dataset-verifiers-v2"
        run["manifest"]["evaluation_profile_hash"] = evaluator_hash(name, dataset)
