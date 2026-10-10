"""Offline public-history cuts; evaluator actions live outside Winner's input tree."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from dwelly_bot.planner.context import history_view, parse_events
from dwelly_bot.storage import file_hash, save_json
from hackathon_winner.adapters import attachment_text, checked_path
from hackathon_winner.export import CASE


def prepare(track: Path, output: Path, specification: Path, availability: Path) -> dict[str, Any]:
    """Two text files per decision: inputs/ID/context.md and references/ID/action.md.

    No learned extraction: the reference retains the exact recorded next action, including
    qualifications. Past-tense operations are exemplars for proposed actions, not evidence
    that the current agent executed them. Attachment access follows the reviewed profile.
    """
    spec = json.loads(specification.read_text())
    profile = json.loads(availability.read_text())
    folders = {p.name: p for p in track.iterdir() if (p / "history.md").is_file()}
    if set(folders) != set(spec["decision_events"]):
        raise ValueError("Preparation must explicitly cover every source scenario")
    output.mkdir(parents=True, exist_ok=False)
    rows = []
    originals = {}
    for number, points in sorted(spec["decision_events"].items()):
        if not CASE.fullmatch(number) or len(points) != len(set(points)) or not points:
            raise ValueError(f"Invalid decision specification: {number}")
        folder = folders[number]
        history_path = checked_path(folder / "history.md", track)
        history = history_path.read_text()
        originals[f"{number}/history.md"] = file_hash(history_path)
        events = parse_events(history)
        if [e.id for e in events] != [f"event-{i:03d}" for i in range(1, len(events) + 1)]:
            raise ValueError(f"Noncontiguous/unparsed events: {number}")
        attachment_rules = {r["path"]: r for r in profile["attachments"].get(number, [])}
        actual = {
            str(p.relative_to(folder)): p
            for p in (folder / "attachments").rglob("*")
            if p.is_file()
        }
        if actual.keys() != attachment_rules.keys():
            raise ValueError(f"Unreviewed attachment inventory: {number}")
        for name, path in actual.items():
            checked_path(path, folder)
            originals[f"{number}/{name}"] = file_hash(path)
        for point in points:
            _, visible, at = history_view(history, events=point - 1)
            item = f"{number}-e{point:03d}"
            # A single text document is the black-box Planner boundary. Level-three
            # headings prevent the generic history parser from absorbing attachments
            # into the final timed event; all evidence is cited as context.md.
            context = f"# Case context\n\nObserved through: {at}\n\n" + visible.replace(
                "\n## ", "\n### "
            )
            if context.startswith("## "):
                raise AssertionError("Context must have a neutral heading")
            context = context.replace("\n\n## ", "\n\n### ")
            included, withheld = [], []
            for name, path in sorted(actual.items()):
                rule = attachment_rules[name]
                if rule["available_after_event"] <= point - 1:
                    content = attachment_text(path)
                    if content.startswith("[Attachment unread:"):
                        raise ValueError(f"Cannot extract available evidence: {number}/{name}")
                    context += f"\n### Available attachment: {name}\n\n{content}\n"
                    included.append(name)
                else:
                    withheld.append(name)
            event = events[point - 1]
            action = (
                "# Expected next action — public historical example\n\n"
                f"Channel: {event.channel}\nActor: {event.sender}\nTarget: {event.recipient}\n\n"
                "Perform the operational action or communicate the supported result described below. "
                "Treat completed-tense wording as an example of the intended action, not proof of "
                "execution by the evaluated agent. Respect prerequisites absent from the context.\n\n"
                + event.text
                + "\n"
            )
            input_path = output / "inputs" / item / "context.md"
            reference_path = output / "references" / item / "action.md"
            for path, body in ((input_path, context), (reference_path, action)):
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(body)
            rows.append(
                {
                    "id": item,
                    "scenario": number,
                    "decision_event": point,
                    "visible_events": point - 1,
                    "decision_time": at,
                    "context": str(input_path.relative_to(output)),
                    "context_sha256": file_hash(input_path),
                    "reference": str(reference_path.relative_to(output)),
                    "reference_sha256": file_hash(reference_path),
                    "reference_event": event.model_dump(),
                    "attachments_included": included,
                    "attachments_withheld": withheld,
                }
            )
    result = {
        "version": 1,
        "population": "public development examples",
        "specification": spec,
        "availability": profile,
        "source_files": originals,
        "scenarios": len(folders),
        "cases": rows,
    }
    save_json(output / "manifest.json", result)
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--track", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--specification", type=Path, required=True)
    parser.add_argument("--availability", type=Path, required=True)
    args = parser.parse_args()
    result = prepare(args.track, args.output, args.specification, args.availability)
    print(f"{result['scenarios']} scenarios -> {len(result['cases'])} decision cases")


if __name__ == "__main__":
    main()
