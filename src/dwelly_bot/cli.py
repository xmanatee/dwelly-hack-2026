"""Common entry point for operational execution, experiments and local analytics."""

import argparse
import os
import sys
from collections.abc import Callable, Sequence
from importlib import import_module
from typing import cast

COMMANDS = {
    "service": ("service.cli", "Authenticated text/voice adapter with durable sessions"),
    "local": ("local_cli", "Run the product pipeline with the synthetic banking world"),
    "actions": ("planning.cli", "Print production/contest action JSON schemas"),
    "demo": ("demo_cli", "Run the offline trigger/context/planner/mock-execution pipeline"),
    "run": ("experiments.agent_cli", "Run the common agent with a selected dataset adapter"),
    "agent": ("experiments.agent_cli", "Execute cases or inspect dataset/provider readiness"),
    "experiment": ("experiments.cli", "Run, grade, render or compare saved experiments"),
    "analyze": ("analysis.cli", "Run analysis recipes or render their saved results"),
    "data": ("data", "Pin supplied dataset bytes"),
    "plan": ("planner.cli", "Run the planner alone on JSON inputs or dataset cases"),
    "export": ("reporting.submission", "Export faithful ANSWERS from a saved run"),
    "monitor": ("reporting.monitor", "Serve local live status on loopback"),
}


def main(argv: Sequence[str] | None = None) -> int:
    arguments = list(sys.argv[1:] if argv is None else argv)
    os.environ["LOGFIRE_SEND_TO_LOGFIRE"] = "false"
    os.environ["OTEL_SDK_DISABLED"] = "true"
    os.environ["PYDANTIC_AI_NO_BANNER"] = "1"
    if arguments and arguments[0] in COMMANDS:
        module, _ = COMMANDS[arguments[0]]
        command = cast(Callable[[Sequence[str]], int], import_module("dwelly_bot." + module).main)
        return command(arguments if arguments[0] == "run" else arguments[1:])
    if arguments == ["check"]:
        from dwelly_bot.checks import check

        return check()
    parser = argparse.ArgumentParser(
        prog="dwelly-bot", description="dwelly-bot operational agent and experiments."
    )
    commands = parser.add_subparsers(dest="command")
    for name, (_, description) in COMMANDS.items():
        commands.add_parser(name, help=description)
    commands.add_parser("check", help="Offline lint, type and test gate")
    parser.parse_args(arguments)
    parser.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
