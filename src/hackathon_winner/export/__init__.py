"""Write the two contest files per case, plus the plan and generator input for audit."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from pydantic import BaseModel

from dwelly_bot.storage import save_json
from hackathon_winner.generation import Generated

CASE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")


def check_output(directory: Path, *, development: bool) -> None:
    """Practice cases never go to ANSWERS; existing answers are never overwritten."""
    if development and any(p.name.upper() == "ANSWERS" for p in (directory, *directory.parents)):
        raise ValueError(
            "Public practice cases cannot be written to ANSWERS; use a review directory"
        )
    if directory.exists() and any(p.name != "README.md" for p in directory.iterdir()):
        raise ValueError("Write into an empty directory; existing answers are never overwritten")


def prepare_output(directory: Path, *, development: bool) -> None:
    """Exclusively claim a run directory before journals or model calls are started."""
    check_output(directory, development=development)
    directory.mkdir(parents=True, exist_ok=True)
    try:
        with (directory / ".winner-run").open("x", encoding="utf-8") as stream:
            stream.write("Reserved by Hackathon Winner; retain this marker with the run.\n")
    except FileExistsError as exc:
        raise ValueError("Another Winner run has already claimed this output directory") from exc


def write_case(
    directory: Path,
    case_id: str,
    generated: Generated,
    *,
    plan: BaseModel,
    context: str,
    generator: dict[str, Any],
) -> Path:
    if not CASE.fullmatch(case_id):
        raise ValueError(f"Unsafe case identifier {case_id!r}")
    target = directory / case_id
    target.mkdir(parents=True, exist_ok=False)
    (target / "ANSWER.md").write_text(generated.rendered_answer.strip() + "\n")
    (target / "REASONING.md").write_text(generated.reasoning.strip() + "\n")
    (target / "context.md").write_text(context.strip() + "\n")
    save_json(target / "plan.json", plan.model_dump(mode="json"))
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
