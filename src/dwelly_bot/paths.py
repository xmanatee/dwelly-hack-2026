"""Local project ownership; generated state stays under experiment artifacts."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DATASET = ROOT / "dataset"

ARTIFACTS = ROOT / "experiments/baseline/artifacts"
PACKAGE = Path(__file__).resolve().parent


def default_ledger() -> Path:
    return ROOT / ".cache/accounts/default.json"
