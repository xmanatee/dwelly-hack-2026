"""Print the planner's effective action schemas without a model call."""

import argparse
import json
from collections.abc import Sequence
from pathlib import Path

from dwelly_bot.planning.catalog import ActionProfile
from dwelly_bot.storage import save_json


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Export planner action JSON schemas")
    parser.add_argument("--profile", choices=("production", "contest"), default="production")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args(argv)
    catalog = ActionProfile.load(args.profile).catalog()
    if args.output:
        save_json(args.output, catalog)
    else:
        print(json.dumps(catalog, ensure_ascii=False, indent=2))
    return 0
