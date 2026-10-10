"""One self-contained HTML page for a predictions directory; reads saved files only."""

from __future__ import annotations

import html
import json
import re
from pathlib import Path
from typing import Any

from dwelly_bot.reporting.theme import TOKENS


def inline(text: str) -> str:
    text = html.escape(text)
    text = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", text)
    return re.sub(r"`([^`]+)`", r"<code>\1</code>", text)


def markdown(text: str) -> str:
    """Headings, lists and paragraphs; everything is escaped first."""
    out: list[str] = []
    lists: list[str] = []
    paragraph: list[str] = []

    def flush() -> None:
        if paragraph:
            out.append("<p>" + inline(" ".join(paragraph)) + "</p>")
            paragraph.clear()
        while lists:
            out.append(f"</{lists.pop()}>")

    for line in text.splitlines():
        stripped = line.strip()
        heading = re.match(r"(#{1,4})\s+(.*)", stripped)
        item = re.match(r"(?:[-*]|\d+\.)\s+(.*)", stripped)
        if not stripped:
            flush()
        elif heading:
            flush()
            level = min(len(heading[1]) + 2, 6)
            out.append(f"<h{level}>{inline(heading[2])}</h{level}>")
        elif item:
            if paragraph:
                out.append("<p>" + inline(" ".join(paragraph)) + "</p>")
                paragraph.clear()
            kind = "ol" if stripped[0].isdigit() else "ul"
            if not lists:
                lists.append(kind)
                out.append(f"<{kind}>")
            out.append(f"<li>{inline(item[1])}</li>")
        else:
            paragraph.append(stripped)
    flush()
    return "\n".join(out)


def badge(text: str, tone: str = "") -> str:
    return f'<span class="badge {tone}">{html.escape(text)}</span>'


def case_section(folder: Path, summary: dict[str, Any]) -> str:
    record = json.loads((folder / "generation.json").read_text())
    plan = record.get("plan") or {}
    answer = (folder / "ANSWER.md").read_text()
    reasoning = (folder / "REASONING.md").read_text()
    ok = summary.get("planner") == "available" and not str(summary.get("generator", "")).endswith(
        "_error"
    )
    flags = plan.get("safety_flags") or []
    tags = [
        badge(summary.get("planner", "?"), "" if ok else "bad"),
        *(
            [badge(str(summary["generator"]), "bad")]
            if str(summary.get("generator", "")).endswith("_error")
            else []
        ),
        *(
            [badge(plan["expected_disposition"], "info")]
            if plan.get("expected_disposition")
            else []
        ),
        *(badge(flag, "warn") for flag in flags),
    ]
    steps = "".join(
        f"<tr><td>{html.escape(s['id'])}</td><td>{html.escape(s['kind'])}</td>"
        f"<td><code>{html.escape(s['action'])}</code></td>"
        f"<td>{html.escape(s.get('target') or '')}</td><td>{html.escape(s['purpose'])}</td></tr>"
        for s in plan.get("steps", [])
    )
    plan_block = (
        f"<p><strong>Intent:</strong> {html.escape(plan.get('intent', ''))}<br>"
        f"<strong>Identity/authority:</strong> {html.escape(plan.get('identity_authority', ''))}</p>"
        f"<table><thead><tr><th>Step</th><th>Kind</th><th>Action</th><th>Target</th><th>Purpose</th>"
        f"</tr></thead><tbody>{steps}</tbody></table>"
        if steps
        else f"<p>{html.escape(plan.get('error', 'No plan.'))}</p>"
    )
    title = html.escape(plan.get("summary") or plan.get("error") or "")
    search = html.escape(
        f"{folder.name} {plan.get('intent', '')} {' '.join(flags)} {answer}".lower()
    )
    return f"""
<details class="case" data-search="{search}" data-ok="{int(ok)}" data-flagged="{int(bool(flags))}">
<summary><span class="id">{html.escape(folder.name)}</span>{"".join(tags)}<span class="title">{title}</span></summary>
<div class="grid">
<section><h3>ANSWER.md</h3>{markdown(answer)}</section>
<section><h3>REASONING.md</h3>{markdown(reasoning)}</section>
</div>
<section><h3>Plan</h3>{plan_block}</section>
<section><h3>Supplied case history</h3><pre>{html.escape(record.get("context", ""))}</pre></section>
<p class="muted">{summary.get("requests", 0)} model requests · API-equivalent ${summary.get("cost_usd", 0):.4f} · generator: {html.escape(str(summary.get("generator")))}</p>
</details>"""


def render(directory: Path, output: Path | None = None) -> Path:
    meta = json.loads((directory / "predictions.json").read_text())
    rows = {row["case_id"]: row for row in meta["cases"]}
    folders = [directory / case_id for case_id in rows if (directory / case_id).is_dir()]
    available = sum(row["planner"] == "available" for row in rows.values())
    cost = sum(row["cost_usd"] for row in rows.values())
    scope = (
        "Public practice cases, not a submission"
        if meta.get("development", True)
        else "Supplied cases; official eligibility is not inferred"
    )
    t = TOKENS
    page = f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Case predictions</title>
<style>
:root{{--ink:{t["ink"]};--muted:{t["muted"]};--line:{t["line"]};--paper:{t["paper"]};--surface:{t["surface"]};
--accent:{t["accent"]};--red:{t["red"]};--amber:{t["amber"]};--blue:{t["blue"]};--soft:{t["soft"]};
--bad:{t["fail-soft"]};--warn:{t["warn-soft"]}}}
@media (prefers-color-scheme:dark){{:root{{--ink:#e7ece6;--muted:#a3ada6;--line:#2c3430;--paper:#141917;
--surface:#1b211e;--soft:#22302a;--bad:#4a2723;--warn:#41391f}}}}
*{{box-sizing:border-box}}body{{margin:0;background:var(--paper);color:var(--ink);font:15px/1.55 {t["font"]}}}
main{{max-width:1180px;margin:auto;padding:24px 16px}}h1{{margin:0 0 4px;font-size:24px}}
.muted{{color:var(--muted);font-size:13px}}.stats{{display:flex;gap:12px;flex-wrap:wrap;margin:16px 0}}
.stat{{background:var(--surface);border:1px solid var(--line);border-radius:{t["radius"]};padding:10px 14px}}
.stat b{{display:block;font-size:20px}}.controls{{display:flex;gap:8px;flex-wrap:wrap;margin-bottom:12px}}
input,select{{font:inherit;padding:8px 10px;border:1px solid var(--line);border-radius:8px;background:var(--surface);color:var(--ink)}}
input{{flex:1;min-width:200px}}
.case{{background:var(--surface);border:1px solid var(--line);border-radius:{t["radius"]};margin:8px 0;padding:0 14px}}
.case summary{{cursor:pointer;padding:12px 0;display:flex;gap:8px;align-items:baseline;flex-wrap:wrap}}
.id{{font-weight:600;font-family:ui-monospace,monospace}}.title{{color:var(--muted);flex-basis:100%}}
.badge{{font-size:12px;padding:1px 8px;border-radius:999px;background:var(--soft);color:var(--accent)}}
.badge.bad{{background:var(--bad);color:var(--red)}}.badge.warn{{background:var(--warn);color:var(--amber)}}
.badge.info{{color:var(--blue)}}.grid{{display:grid;grid-template-columns:1fr 1fr;gap:16px}}
@media (max-width:760px){{.grid{{grid-template-columns:1fr}}}}
section h3{{font-size:13px;text-transform:uppercase;letter-spacing:.04em;color:var(--muted);margin:14px 0 6px}}
section h3+h3,section h4,section h5{{margin:10px 0 4px}}
pre{{white-space:pre-wrap;background:var(--soft);padding:10px;border-radius:8px;font-size:13px;max-height:420px;overflow:auto}}
table{{border-collapse:collapse;width:100%;font-size:13px}}td,th{{border-top:1px solid var(--line);padding:6px;text-align:left;vertical-align:top}}
code{{font-size:12px;background:var(--soft);padding:1px 4px;border-radius:4px}}
</style></head><body><main>
<h1>Case predictions</h1>
<p class="muted">{html.escape(str(directory))} · {scope}. Planned actions are proposals; nothing was executed. Full-history predictions are not a blind decision-point evaluation.</p>
<div class="stats">
<div class="stat"><b>{len(rows)}</b>cases</div>
<div class="stat"><b>{available}</b>plans available</div>
<div class="stat"><b>{sum(row["requests"] for row in rows.values())}</b>model requests</div>
<div class="stat"><b>${cost:.2f}</b>API-equivalent</div>
</div>
<div class="controls"><input id="q" placeholder="Search cases, intents, flags, answers" aria-label="Search">
<select id="f" aria-label="Filter"><option value="">All cases</option><option value="flagged">Safety flags</option>
<option value="failed">Processing errors</option></select>
<button onclick="document.querySelectorAll('.case').forEach(d=>d.open=!d.open)">Expand/collapse</button></div>
{"".join(case_section(folder, rows[folder.name]) for folder in folders)}
</main><script>
const q=document.getElementById('q'),f=document.getElementById('f');
function apply(){{const t=q.value.toLowerCase();document.querySelectorAll('.case').forEach(d=>{{
const show=d.dataset.search.includes(t)&&(!f.value||(f.value==='flagged'&&d.dataset.flagged==='1')||(f.value==='failed'&&d.dataset.ok==='0'));
d.style.display=show?'':'none';}});}}
q.addEventListener('input',apply);f.addEventListener('change',apply);
</script></body></html>"""
    target = output or directory / "report.html"
    target.write_text(page)
    return target
