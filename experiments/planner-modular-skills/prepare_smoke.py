"""Prepare fixed decision snapshots without importing evaluation labels or future replies."""

import json
from contextlib import closing
from pathlib import Path

from dwelly_bot.adapters.synthetic_banking.sources import connect
from dwelly_bot.planner import PlanInput
from dwelly_bot.planner.context import history_view, parse_events
from dwelly_bot.planner.contracts import PlanEvent
from dwelly_bot.storage import file_hash

ROOT = Path(__file__).resolve().parents[2]
OUTPUT = Path(__file__).parent / "artifacts/inputs"


def main() -> None:
    OUTPUT.mkdir(parents=True, exist_ok=False)
    receipt: list[dict[str, object]] = []
    original = ROOT / ".cache/datasets/banking-reviewed/original/Banking & Financial Services"
    safety = ROOT / "experiments/safety-cases/Banking & Financial Services"
    for prefix, directory, case, count in [
        ("public", original, "001", 4),
        ("public", original, "042", 4),
        ("safety", safety, "107", 1),
        ("safety", safety, "109", 1),
        ("safety", safety, "126", 1),
    ]:
        history = directory / case / "history.md"
        request, visible, at = history_view(history.read_text(), events=count)
        source = PlanInput(
            case_id=f"{prefix}-{case}",
            decision_time=at,
            request=request,
            events=parse_events(visible),
            task="Plan the next supported response; no bank actions execute.",
        )
        (OUTPUT / f"{source.case_id}.input.json").write_text(source.model_dump_json(indent=2))
        receipt.append(
            {
                "case_id": source.case_id,
                "history": str(history.relative_to(ROOT)),
                "sha256": file_hash(history),
                "visible_events": count,
                "attachments": "withheld",
            }
        )
    database = ROOT / "local_testing/banking/data/seed-2026/state/decision.sqlite"
    with closing(connect(database)) as db:
        for case in ("SYN-0077", "SYN-0421"):
            rows = db.execute(
                "SELECT * FROM messages WHERE scope_id=? ORDER BY seq", (case,)
            ).fetchall()
            events = [
                PlanEvent(
                    id=f"event-{r['seq']:03}",
                    at=r["at"],
                    channel=r["channel"],
                    sender=r["sender"],
                    recipient=r["recipient"],
                    text=r["body"],
                )
                for r in rows
            ]
            source = PlanInput(
                case_id=case,
                decision_time=events[-1].at,
                request=events[-1].text,
                events=events,
                task="Plan from these supplied messages; bank records and attachments were not supplied.",
            )
            (OUTPUT / f"{case}.input.json").write_text(source.model_dump_json(indent=2))
            receipt.append(
                {
                    "case_id": case,
                    "database": str(database.relative_to(ROOT)),
                    "sha256": file_hash(database),
                    "visible_events": len(events),
                    "scope": "messages only",
                }
            )
    (OUTPUT.parent / "input-receipt.json").write_text(json.dumps(receipt, indent=2) + "\n")


if __name__ == "__main__":
    main()
