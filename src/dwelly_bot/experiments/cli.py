"""One command surface for execution, saved grading, reports and judge calibration."""

from __future__ import annotations

import argparse
import asyncio
import sys
from collections.abc import Sequence


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="dwelly-bot experiment")
    parser.add_argument(
        "action",
        choices=[
            "run",
            "combine",
            "evaluate",
            "report",
            "compare",
            "baseline",
            "calibrate",
            "batch",
        ],
    )
    arguments = list(sys.argv[1:] if argv is None else argv)
    if not arguments or arguments[0] in ["-h", "--help"]:
        parser.print_help()
        return 0
    args = parser.parse_args(arguments[:1])
    remaining = arguments[1:]
    if args.action == "run":
        from dwelly_bot.experiments.comparison import run

        return asyncio.run(run(remaining))
    if args.action in {"compare", "baseline"}:
        from dwelly_bot.experiments.comparison import baseline, compare

        return (compare if args.action == "compare" else baseline)(remaining)
    if args.action == "combine":
        from dwelly_bot.evaluation.attempts import main as combine

        return combine(remaining)
    if args.action == "batch":
        from dwelly_bot.evaluation.batch import main as batch

        return batch(remaining)
    if args.action == "evaluate":
        from dwelly_bot.evaluation.runner import main as evaluate

        return asyncio.run(evaluate(remaining))
    elif args.action == "calibrate":
        from dwelly_bot.evaluation.calibration import main as calibrate

        return asyncio.run(calibrate(remaining))
    else:
        from dwelly_bot.reporting.html import main as report

        report(remaining)
    return 0
