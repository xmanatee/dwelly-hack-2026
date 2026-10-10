"""Archive actual execution/evaluation bytes and render saved results, without model calls."""

from __future__ import annotations

import shutil
from pathlib import Path

from dwelly_bot.reporting.winner_evaluation import render
from dwelly_bot.storage import file_hash, load_json, save_json

ROOT = Path(__file__).parent


def main() -> None:
    work = ROOT / "artifacts"
    bundle = load_json(work / "graded/results.json.gz")
    files = {}
    for directory in (work / "prepared", work / "winner"):
        for path in sorted(directory.rglob("*")):
            if path.is_file() and path.suffix != ".html":
                files[str(path.relative_to(work))] = path.read_text()
    files["execution-receipt.json"] = (work / "execution-receipt.json").read_text()
    save_json(ROOT / "captures.json.gz", {"files": files})
    shutil.copyfile(work / "graded/results.json.gz", ROOT / "results.json.gz")
    render(bundle, ROOT / "report.html")
    save_json(
        ROOT / "verification.json",
        {
            "execution": load_json(work / "execution-receipt.json"),
            "summary": bundle["summary"],
            "captured_files": len(files),
            "captures_sha256": file_hash(ROOT / "captures.json.gz"),
            "results_sha256": file_hash(ROOT / "results.json.gz"),
            "limitations": [
                "Public development population used previously for skills; not a blind holdout.",
                "Decision points within a source scenario are correlated.",
                "Historical next actions are examples, not independently annotated unique ground truth.",
                "Sonnet subject and Opus judge are different models from the same vendor family.",
                "No real bank tools or effects; proposed actions only.",
                "No comparison or baseline adoption is implied by this control run.",
            ],
        },
    )
    print(ROOT / "report.html")


if __name__ == "__main__":
    main()
