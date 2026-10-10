"""Corpus receipts must cover actual bytes; variant prompts must not change verifier identity."""

import hashlib
import json
import shutil
from pathlib import Path

import pytest

from dwelly_bot.experiments import provenance
from dwelly_bot.paths import ROOT


def receipt(root: Path) -> Path:
    root.mkdir()
    payload = b"public fixture"
    (root / "data.txt").write_bytes(payload)
    (root / "source.json").write_text(
        json.dumps(
            {
                "files": [
                    {
                        "path": "data.txt",
                        "sha256": hashlib.sha256(payload).hexdigest(),
                        "bytes": len(payload),
                    }
                ]
            }
        )
    )
    return root


def test_dataset_hash_rejects_modified_actual_file(tmp_path: Path) -> None:
    dataset = receipt(tmp_path / "dataset")
    original = provenance.dataset_hash(dataset)
    (dataset / "README.md").write_text("Installation instructions")
    (dataset / "fetch.py").write_text("# Bootstrap script")
    assert provenance.dataset_hash(dataset) == original
    (dataset / "data.txt").write_text("different bytes")
    with pytest.raises(ValueError, match="integrity mismatch"):
        provenance.dataset_hash(dataset)


def test_dataset_receipt_cannot_follow_outside_symlink(tmp_path: Path) -> None:
    dataset = receipt(tmp_path / "dataset")
    (tmp_path / "outside.txt").write_text("public fixture")
    (dataset / "data.txt").unlink()
    (dataset / "data.txt").symlink_to(tmp_path / "outside.txt")
    with pytest.raises(ValueError, match="escapes"):
        provenance.dataset_hash(dataset)


def test_unpinned_evidence_cannot_hide_behind_an_unchanged_receipt(tmp_path: Path) -> None:
    dataset = receipt(tmp_path / "dataset")
    (dataset / "extra.pdf").write_bytes(b"additional case evidence")
    with pytest.raises(ValueError, match=r"unpinned files.*extra\.pdf"):
        provenance.dataset_hash(dataset)


def test_verifier_identity_excludes_model_config_and_runtime_skill(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    dataset = receipt(tmp_path / "dataset")
    root = tmp_path / "solution"
    shutil.copytree(
        ROOT / "src/dwelly_bot",
        root / "src/dwelly_bot",
        ignore=shutil.ignore_patterns("__pycache__"),
    )
    module = root / "src/dwelly_bot/adapters/banking.py"
    module.write_text('CHECK = "independent domain checker"\n')
    shared_checker = root / "src/dwelly_bot/evaluation/checks.py"
    shared_checker.write_text('CHECK = "shared independent predicates"\n')
    (root / "configs").mkdir()
    monkeypatch.setattr(provenance, "ROOT", root)
    monkeypatch.setattr(
        "dwelly_bot.experiments.provenance.inspect.getfile", lambda _cls: str(module)
    )
    before = provenance.evaluator_hash("dwelly-banking", dataset)
    (root / "configs/variant.json").write_text('{"model":"different"}')
    (root / "src/dwelly_bot/skills/banking.md").write_text("changed subject guidance")
    assert provenance.evaluator_hash("dwelly-banking", dataset) == before
    shared_checker.write_text('CHECK = "changed shared independent predicates"\n')
    assert provenance.evaluator_hash("dwelly-banking", dataset) != before
    shared_checker.write_text('CHECK = "shared independent predicates"\n')
    module.write_text('CHECK = "changed independent checker"\n')
    assert provenance.evaluator_hash("dwelly-banking", dataset) != before


def test_source_receipt_includes_shared_package_locks_without_credentials() -> None:
    files = provenance.source_files()
    assert {"pyproject.toml", "uv.lock"} <= files.keys()
    assert "src/dwelly_bot/skills/banking.md" in files
    assert all(path.name != ".env" for path in files.values())
