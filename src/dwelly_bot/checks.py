"""Repeatable offline quality gate for a package and its local smoke flow."""

import subprocess
import sys
from pathlib import Path

from dwelly_bot.paths import ROOT


def check(*, root: Path = ROOT) -> int:
    sources = ("src", "tests", "experiments/controls", "dataset/fetch.py")
    for module, arguments in [
        ("ruff", ["check", *sources]),
        ("ruff", ["format", "--check", *sources]),
        ("mypy", []),
        ("pytest", ["-q"]),
    ]:
        result = subprocess.run([sys.executable, "-m", module, *arguments], cwd=root, check=False)
        if result.returncode:
            return result.returncode
    return 0
