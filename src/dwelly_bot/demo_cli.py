"""Local fixture-driven vertical slice. This command never initializes a model."""

import argparse
import asyncio
from collections.abc import Sequence
from pathlib import Path

from pydantic import TypeAdapter

from dwelly_bot.channels.intake import inbound_adapter
from dwelly_bot.context.collector import ContextCollector, ContextRecord, InMemorySource
from dwelly_bot.execution import MockExecutor
from dwelly_bot.harness.production import ProductionPipeline
from dwelly_bot.planning import HumanReviewPlanner


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Run a local mock pipeline; no model or external actions."
    )
    parser.add_argument("--input", required=True, type=Path, help="Email, call or ticket JSON")
    parser.add_argument("--records", type=Path, help="Optional array of case-scoped source records")
    parser.add_argument(
        "--output", required=True, type=Path, help="New capture directory (must not exist)"
    )
    args = parser.parse_args(argv)
    try:
        event = inbound_adapter.validate_json(args.input.read_text())
        records = (
            TypeAdapter(tuple[ContextRecord, ...]).validate_json(args.records.read_text())
            if args.records
            else ()
        )
        pipeline = ProductionPipeline(
            ContextCollector((InMemorySource(records),)), HumanReviewPlanner(), MockExecutor()
        )
        result = asyncio.run(pipeline.run(event, args.output))
    except (OSError, ValueError) as exc:
        parser.exit(2, f"Demo failed: {exc}\n")
    print(f"MOCK {result.status}: {args.output / 'result.json'}")
    for receipt in result.receipts:
        print(f"  {receipt.status}: {receipt.operation} -> {receipt.target}")
    return 1 if result.status == "failed" else 0


if __name__ == "__main__":
    raise SystemExit(main())
