"""Run the actual product pipeline against a prepared local banking world."""

from __future__ import annotations

import argparse
import asyncio
import json
import re
import sqlite3
from collections.abc import Sequence
from contextlib import closing
from pathlib import Path

from dwelly_bot.adapters.synthetic_banking.sources import bank_sources, connect
from dwelly_bot.channels.intake import Inbound, inbound_adapter
from dwelly_bot.demo_cli import FixturePlanner
from dwelly_bot.harness.local import run_local_pipeline
from dwelly_bot.planning import HumanReviewPlanner, Plan, Planner
from dwelly_bot.storage import file_hash, save_json


def local_event(dataset: Path, case: str, channel: str | None = None) -> Inbound:
    if not re.fullmatch(r"SYN-\d{4,}", case):
        raise ValueError("Use a case ID from local list, e.g. SYN-0001")
    event = inbound_adapter.validate_json((dataset / "cases" / f"{case}.json").read_text())
    if channel is None or channel == event.channel:
        return event
    with closing(connect(dataset / "state" / "decision.sqlite")) as db:
        contact = db.execute("SELECT * FROM contacts WHERE scope_id=?", (case,)).fetchone()
    if contact is None:
        raise ValueError("No local route for this case")
    data = event.model_dump(include={"event_id", "scope_id", "received_at", "text", "hints"})
    data.update(channel=channel, event_id=f"{event.event_id}-{channel}")
    data["text"] = (
        f"Local transport replay as {channel}; original evidence follows.\n\n{event.text}"
    )
    if channel == "email":
        data.update(sender=contact["email"], thread_id=f"thread-{case}")
    elif channel == "call":
        data.update(caller=contact["phone"], session_id=f"call-{case}", active=True)
    else:
        data.update(ticket_id=case)
    return inbound_adapter.validate_python(data)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    listing = commands.add_parser("list", help="List incoming cases; no evaluator labels")
    listing.add_argument(
        "--dataset", type=Path, default=Path("local_testing/banking/data/seed-2026")
    )
    listing.add_argument("--limit", type=int, default=20)
    run = commands.add_parser("run", help="Run context, Planner and mock executor")
    run.add_argument("--dataset", type=Path, default=Path("local_testing/banking/data/seed-2026"))
    select = run.add_mutually_exclusive_group(required=True)
    select.add_argument("--case")
    select.add_argument("--input", type=Path, help="Custom trusted local trigger JSON")
    run.add_argument(
        "--channel",
        choices=("email", "call", "ticket"),
        help="Replay case in another local transport",
    )
    run.add_argument("--context-config", type=Path, help="Enable paid Pydantic AI context research")
    run.add_argument("--plan", type=Path, help="Explicit fixture plan; default is human review")
    run.add_argument(
        "--state", type=Path, help="Mock receipts; default is isolated by dataset hash"
    )
    run.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        manifest = json.loads((args.dataset / "manifest.json").read_text())
        db_path = args.dataset / "state" / "decision.sqlite"
        if (
            manifest["format"] != "dwelly-synthetic-bank-v1"
            or file_hash(db_path) != manifest["runtime_sha256"]
            or manifest.get("read_query_policy_sha256")
            != file_hash(Path(__file__).parent / "adapters/synthetic_banking/read_queries.json")
        ):
            raise ValueError(
                "Dataset manifest/runtime hash mismatch; rebuild into a fresh directory"
            )
        if args.command == "list":
            for path in sorted((args.dataset / "cases").glob("SYN-*.json"))[: max(0, args.limit)]:
                event = inbound_adapter.validate_json(path.read_text())
                print(f"{event.scope_id}  {event.channel:6}  {event.hints.name}")
            return 0
        if args.state is None:
            args.state = Path(".cache/local-bank") / manifest["runtime_sha256"] / "receipts.sqlite"
        if args.input and args.channel:
            raise ValueError(
                "--channel applies to --case; custom JSON already specifies its channel"
            )
        event = (
            inbound_adapter.validate_json(args.input.read_text())
            if args.input
            else local_event(args.dataset, args.case, args.channel)
        )
        if args.state.resolve().is_relative_to(args.dataset.resolve()):
            raise ValueError("Receipt state must be outside the dataset")
        if args.output.resolve().is_relative_to(args.dataset.resolve()):
            raise ValueError("Capture directory must be outside the dataset")
        if any(
            args.state.resolve() == p.resolve()
            for p in (args.input, args.plan, args.context_config)
            if p
        ):
            raise ValueError("Receipt state must be separate from input/config files")
        with closing(connect(db_path)) as db:
            snapshot = db.execute(
                "SELECT as_of FROM snapshots WHERE scope_id=?", (event.scope_id,)
            ).fetchone()
        if snapshot is None:
            raise ValueError("No local scenario for this trusted scope")
        from datetime import datetime

        if event.received_at < datetime.fromisoformat(snapshot["as_of"]):
            raise ValueError("Trigger precedes this scenario snapshot")
        planner: Planner = (
            FixturePlanner(Plan.model_validate_json(args.plan.read_text()))
            if args.plan
            else HumanReviewPlanner()
        )
        result = asyncio.run(
            run_local_pipeline(
                event,
                bank_sources(args.dataset),
                planner,
                args.output,
                state=args.state,
                context_config=args.context_config,
            )
        )
        save_json(args.output / "dataset.json", manifest)
        print(f"MOCK {result.status}: {args.output / 'context.md'} → plan.json → result.json")
        return 1 if result.status == "failed" else 0
    except (OSError, ValueError, sqlite3.Error) as exc:
        parser.exit(2, f"Local bank failed: {exc}\n")


if __name__ == "__main__":
    raise SystemExit(main())
