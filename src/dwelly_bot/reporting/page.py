"""One document shell, theme and component library; output remains a portable HTML file."""

import base64
import gzip
import html
import json
import re
from pathlib import Path
from typing import Any, Literal

from dwelly_bot.reporting.models import Report
from dwelly_bot.reporting.theme import DISPLAY, css, styled
from dwelly_bot.resources import text
from dwelly_bot.storage import write_bytes


def document(
    view: Literal["report", "monitor", "site"],
    title: str,
    data: Any = None,
    *,
    charts: bool = False,
    body: str | None = None,
) -> str:
    library = ""
    if charts:
        from plotly.offline import get_plotlyjs

        library = "<script>" + get_plotlyjs().replace("</script", "<\\/script") + "</script>"
    payload = json.dumps(data, ensure_ascii=False, allow_nan=False, separators=(",", ":"))
    if view == "report" and len(payload) > 1_000_000:
        payload = json.dumps(
            {
                "encoding": "gzip-base64",
                "data": base64.b64encode(gzip.compress(payload.encode(), mtime=0)).decode(),
            }
        )
    payload = (
        payload.replace("<", "\\u003c").replace("\u2028", "\\u2028").replace("\u2029", "\\u2029")
    )
    scripts = ""
    if view != "site":
        scripts = (
            f'<script id="report-data" type="application/json">{payload}</script>'
            + library
            + "<script>const DISPLAY = Object.freeze("
            + json.dumps(DISPLAY)
            + ");\n"
            + text("reporting/assets/ui.js")
            + (
                text("reporting/assets/case.js") + text("reporting/assets/experiment.js")
                if view == "report"
                else ""
            )
            + text(f"reporting/assets/{view}.js")
            + "</script>"
        )
    values = {
        "VIEW": view,
        "TITLE": html.escape(title),
        "BODY": body if body is not None else text(f"reporting/templates/{view}.html"),
        "CSS": css()
        + text("reporting/assets/components.css")
        + (text("reporting/assets/report.css") if view == "site" else "")
        + text(f"reporting/assets/{view}.css"),
        "CONNECT": "'self'" if view == "monitor" else "'none'",
        "SCRIPTS": scripts,
    }
    # Substitute once: supplied text never becomes a template directive.
    return re.sub(
        r"__([A-Z_]+)__", lambda match: values[match[1]], text("reporting/templates/page.html")
    )


def render(report: Report, output: Path) -> None:
    if output.suffix.lower() not in {".html", ".htm"}:
        raise ValueError("HTML reports require an .html or .htm destination")
    if report.receipt.get("analysis_only") or "source_analyses" in report.receipt:
        from dwelly_bot.analysis.session import validate_analysis

        validate_analysis(report)
    data = report.model_dump(mode="json")
    for block in data["blocks"]:
        if block["kind"] == "chart":
            details = block["data"].pop("details", {})
            block["data"] = json.loads(styled(block["data"]).to_json())
            block["data"]["details"] = details
    charts = any(block.kind == "chart" for block in report.blocks)
    write_bytes(
        output, document("report", report.title, data, charts=charts).encode(), overwrite=True
    )
