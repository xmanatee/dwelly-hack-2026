"""Build the project overview from the current dataset and explicitly saved experiments."""

import asyncio
import html
import re
import shutil
import subprocess
import tempfile
from collections import Counter
from pathlib import Path

from dwelly_bot.analysis.banking import build as analyze
from dwelly_bot.analysis.session import AnalysisContext
from dwelly_bot.configuration import read_settings
from dwelly_bot.experiments.comparison import Comparison, SavedRun
from dwelly_bot.reporting.html import build, comparison_rows, outcomes
from dwelly_bot.reporting.models import ReportProfile
from dwelly_bot.reporting.page import document, render
from dwelly_bot.resources import text
from dwelly_bot.storage import load_json


async def main() -> None:
    output = Path("build/pages")
    if output.exists():
        shutil.rmtree(output)
    output.mkdir(parents=True, exist_ok=True)
    profile = ReportProfile.model_validate(read_settings(Path("experiments/report.toml")))
    cards = []
    reference_path = Path("experiments/baseline/reference.json")
    specs = sorted(Path("experiments").glob("*/spec.json"))
    if specs and not reference_path.is_file():
        raise ValueError("Published experiments require an accepted baseline")
    if reference_path.is_file():
        reference = SavedRun.model_validate(load_json(reference_path))
        entries = [("baseline", "Reference run", reference.load())]
        for path in specs:
            comparison = Comparison.model_validate(load_json(path))
            entries.append((path.parent.name, comparison.description, comparison.bundle()))
        for name, context, bundle in entries:
            run = bundle["runs"][-1]
            render(build(bundle, profile), output / f"{name}.html")
            changes = (
                Counter(row["change"] for row in comparison_rows(bundle))
                if name != "baseline"
                else Counter()
            )
            values = {
                **outcomes(run),
                "name": name,
                "label": run.get("label", name),
                "context": context,
                "budget_blocked": sum(
                    str(c.get("error", "")).startswith("BudgetExceeded:") for c in run["cases"]
                ),
                "role": "Baseline" if name == "baseline" else "Experiment",
                "improved": f"↑ {changes['improved']} improved" if changes else "",
                "regressed": f"↓ {changes['regressed']} regressed" if changes else "",
                "link": "Open run" if name == "baseline" else "Compare",
            }
            values["completed"] = values["assigned"] - values["execution_errors"]
            values["score"] = (
                "Correctness unknown"
                if values["unknown"] == values["assigned"]
                else f"{values['verified']} / {values['assigned']} outcomes verified"
            )
            cards.append(
                text("reporting/templates/site-card.html").format_map(
                    {key: html.escape(str(value)) for key, value in values.items()}
                )
            )
    with tempfile.TemporaryDirectory(prefix="analysis-", dir=output) as scratch:
        ctx = AnalysisContext(
            Path("dataset"),
            Path(scratch) / "analysis",
            Path(".cache/analysis"),
            parameters={"sample": 8},
        )
        shutil.copyfile(ctx.save(await analyze(ctx)), output / "analysis.html")
    revision = subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()
    values = {
        "CARDS": "".join(cards)
        or '<p class="status-note">No banking baseline has been recorded yet.</p>',
        "REVISION": html.escape(revision),
    }
    page = re.sub(
        r"__([A-Z_]+)__", lambda match: values[match[1]], text("reporting/templates/site.html")
    )
    (output / "index.html").write_text(
        document("site", "dwelly-bot · Hackathon project", body=page)
    )
    (output / ".nojekyll").touch()
    print(output)


if __name__ == "__main__":
    asyncio.run(main())
