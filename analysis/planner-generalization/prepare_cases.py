"""Materialize synthetic contrasts; reference invariants never enter Winner inputs."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from dwelly_bot.storage import file_hash, save_json

ROOT = Path(__file__).resolve().parents[2]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output",
        type=Path,
        default=ROOT / "analysis/artifacts/planner-generalization/cases",
    )
    args = parser.parse_args()
    source = Path(__file__).with_name("contrastive-cases.json")
    data = json.loads(source.read_text())
    ids: set[str] = set()
    for pair in data["pairs"]:
        if len(pair["cases"]) != 2 or not pair["relation"]:
            raise ValueError("Every contrast needs two cases and an expected relation")
        for case in pair["cases"]:
            cid = case["id"]
            if cid in ids or not cid.replace("-", "").isalnum():
                raise ValueError(f"Duplicate or unsafe case ID: {cid}")
            if not case["context"].strip() or not case["required"] or not case["forbidden"]:
                raise ValueError(f"Incomplete case: {cid}")
            ids.add(cid)
    # Refuse overwrite: any future run and its inputs must remain reproducible.
    args.output.mkdir(parents=True, exist_ok=False)
    manifest = []
    for pair in data["pairs"]:
        for case in pair["cases"]:
            folder = args.output / "inputs" / case["id"]
            folder.mkdir(parents=True)
            path = folder / "context.md"
            path.write_text(case["context"])
            reference = {k: case[k] for k in ("id", "required", "forbidden")}
            reference.update(pair=pair["id"], relation=pair["relation"])
            save_json(args.output / "references" / f"{case['id']}.json", reference)
            manifest.append({"id": case["id"], "input_sha256": file_hash(path), "pair": pair["id"]})
    save_json(
        args.output / "manifest.json",
        {
            "source_sha256": file_hash(source),
            "cases": manifest,
            "status": "prepared_only_not_evaluated",
            "new_model_calls": 0,
        },
    )
    print(args.output / "inputs")


if __name__ == "__main__":
    main()
