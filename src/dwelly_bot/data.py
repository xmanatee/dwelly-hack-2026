"""Pin the actual supplied corpus before experimentation; no fabricated labels."""

import argparse
from pathlib import Path

from dwelly_bot.storage import file_hash, save_json

BOOTSTRAP_FILES = {"source.json", "README.md", "fetch.py"}


def pin(root: Path) -> None:
    root = root.resolve()
    records = []
    for path in sorted(root.rglob("*")):
        if not path.is_file() or str(path.relative_to(root)) in BOOTSTRAP_FILES:
            continue
        if not path.resolve().is_relative_to(root):
            raise ValueError("Corpus symlink escapes its root")
        records.append(
            {
                "path": str(path.relative_to(root)),
                "bytes": path.stat().st_size,
                "sha256": file_hash(path),
            }
        )
    if not records:
        raise ValueError("Cannot pin an empty dataset")
    save_json(
        root / "source.json",
        {"files": records, "origin": "Supplied local corpus; generated integrity receipt"},
    )


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(prog="dwelly-bot data")
    parser.add_argument("action", choices=["pin"])
    parser.add_argument("root", type=Path)
    args = parser.parse_args(argv)
    pin(args.root)
    print(args.root / "source.json")
    return 0
