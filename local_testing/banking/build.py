"""Build a fresh synthetic world and separate runtime evidence from evaluation data."""

import argparse
import subprocess
import sys
from importlib.metadata import version
from pathlib import Path
from tempfile import TemporaryDirectory

from dwelly_bot.adapters.synthetic_banking.prepare import prepare
from dwelly_bot.storage import file_hash, save_json


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=int, default=2026)
    parser.add_argument("--per-variant", type=int, default=4)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    root = Path(__file__).resolve().parent
    output = (args.output or root / "data" / f"seed-{args.seed}").resolve()
    if output.exists():
        parser.error(f"Output exists; choose a new directory: {output}")
    if args.per_variant < 1:
        parser.error("--per-variant must be positive")
    with TemporaryDirectory(prefix="dwelly-bank-") as scratch:
        original = Path(scratch) / "original"
        subprocess.run(
            [
                sys.executable,
                "-m",
                "synth.build",
                "--out",
                str(original),
                "--seed",
                str(args.seed),
                "--per-variant",
                str(args.per_variant),
            ],
            cwd=root / "generator",
            check=True,
        )
        subprocess.run(
            [sys.executable, "-m", "synth.validate", str(original)],
            cwd=root / "generator",
            check=True,
        )
        manifest = prepare(original, output)
        manifest["build"] = {
            "seed": args.seed,
            "per_variant": args.per_variant,
            "generator_manifest_sha256": file_hash(root / "source.json"),
            "dependencies": {name: version(name) for name in ("reportlab", "pillow", "pypdf")},
        }
        save_json(output / "manifest.json", manifest, overwrite=True)
        print(manifest)
    print(f"Local bank ready: {output}")


if __name__ == "__main__":
    main()
