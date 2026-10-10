"""Write the two contest files per case, plus the plan and generator input for audit."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from dwelly_bot.planning.contracts import Plan
from dwelly_bot.storage import save_json
from hackathon_solver.generation import Generated

CASE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")


def check_output(directory: Path, *, development: bool) -> None:
    """Practice cases never go to ANSWERS; existing answers are never overwritten."""
    if development and directory.name.upper() == "ANSWERS":
        raise ValueError(
            "Public practice cases cannot be written to ANSWERS; use a review directory"
        )
    if directory.exists() and any(p.name != "README.md" for p in directory.iterdir()):
        raise ValueError("Write into an empty directory; existing answers are never overwritten")


def write_case(
    directory: Path,
    case_id: str,
    generated: Generated,
    *,
    plan: Plan,
    context: str,
    generator: dict[str, Any],
) -> Path:
    if not CASE.fullmatch(case_id):
        raise ValueError(f"Unsafe case identifier {case_id!r}")
    target = directory / case_id
    target.mkdir(parents=True, exist_ok=False)
    (target / "ANSWER.md").write_text(generated.answer.strip() + "\n")
    (target / "REASONING.md").write_text(generated.reasoning.strip() + "\n")
    save_json(
        target / "generation.json",
        {
            "case_id": case_id,
            "plan": plan.model_dump(mode="json"),
            "context": context,
            "generator": generator,
            "output": generated.model_dump(),
        },
    )
    return target
