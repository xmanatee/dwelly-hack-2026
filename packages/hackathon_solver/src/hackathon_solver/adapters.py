"""Case folders -> planner input from the full history.md only; no other case file is read."""

from __future__ import annotations

import tempfile
from dataclasses import dataclass
from pathlib import Path

from dwelly_bot.adapters.banking import TRACK, BankingSession
from dwelly_bot.context.documents import Documents
from dwelly_bot.contracts import AgentCase, RunConfig
from dwelly_bot.planner.context import parse_events
from dwelly_bot.planner.contracts import PlanInput

TASK = (
    "Read the full case history. Plan the bank's next action and the expected outcome, "
    "stating what the records do not confirm and which actions need a bank operator."
)


def is_bank(name: str) -> bool:
    return name.lower().startswith(("h&v", "harrow"))


@dataclass
class HistoryCase:
    case_id: str
    number: str
    history: str
    source: PlanInput


def load(
    track: Path, config: RunConfig, *, ids: list[str] | None = None, prefix: str = "banking"
) -> list[HistoryCase]:
    """Every case folder with a history.md, in order; IDs are `<prefix>-<number>`."""
    folders = sorted(p for p in track.iterdir() if (p / "history.md").is_file())
    if ids is not None:
        wanted = set(ids)
        folders = [p for p in folders if f"{prefix}-{p.name}" in wanted]
        if missing := wanted - {f"{prefix}-{p.name}" for p in folders}:
            raise ValueError(f"Unknown case IDs: {sorted(missing)}")
    cases = []
    for folder in folders:
        history = (folder / "history.md").read_text()
        events = parse_events(history)
        if not events:
            raise ValueError(f"{folder.name}: no events parsed from history.md")
        customer = next((e for e in events if not is_bank(e.sender)), None)
        case_id = f"{prefix}-{folder.name}"
        with tempfile.TemporaryDirectory() as directory:
            (Path(directory) / "history.md").write_text(history)
            case = AgentCase(
                id=case_id,
                dataset="dwelly-banking-history",
                title=f"Banking case {folder.name}",
                input={
                    "request": customer.text if customer else "",
                    "organizer_id": folder.name,
                    "track": TRACK,
                    "decision_time": events[-1].at,
                    "visible_events": len(events),
                    "task": TASK,
                    "capabilities": "Read-only case evidence and arithmetic. No bank systems, "
                    "customer messaging or operational write tools are connected.",
                },
            )
            source = BankingSession(case, Documents(Path(directory))).plan_input(config)
        cases.append(HistoryCase(case_id, folder.name, history, source))
    return cases
