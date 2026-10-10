"""Dwelly case folders: the timed history.md and attachment text; index.md is never read."""

import re
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any

from dwelly_bot.analysis import AnalysisContext, Report
from dwelly_bot.analysis.charts import ranking
from dwelly_bot.analysis.discovery_inputs import requested_discovery
from dwelly_bot.analysis.discovery_types import DiscoveryRecord
from dwelly_bot.context.evidence import EvidenceText

TEXT_ATTACHMENTS = {".csv", ".md", ".txt", ".json"}
EVENT = re.compile(
    r"^## (?P<at>[^\n]+?) — event (?P<number>\d+)\n+"
    r"- \*\*Channel:\*\* (?P<channel>[^\n]*)\n"
    r"- \*\*From:\*\* (?P<sender>[^\n]*)\n"
    r"- \*\*To:\*\* (?P<recipient>[^\n]*)\n+"
    r"(?P<body>.*?)(?=\n<a id=|\Z)",
    re.MULTILINE | re.DOTALL,
)


def attachment_text(path: Path) -> str | None:
    if path.suffix.lower() in TEXT_ATTACHMENTS:
        return path.read_text().strip()
    if path.suffix.lower() == ".pdf":
        from pypdf import PdfReader

        return "\n".join(page.extract_text() for page in PdfReader(path).pages).strip()
    return None


def read_case(folder: Path) -> dict[str, Any]:
    history = (folder / "history.md").read_text()
    events = [
        {key: value.strip() for key, value in match.groupdict().items()}
        for match in EVENT.finditer(history)
    ]
    declared = re.search(r"^Total events: (\d+)$", history, re.MULTILINE)
    if declared is None or int(declared.group(1)) != len(events):
        raise ValueError(f"{folder.name}: parsed {len(events)} history events; header disagrees")
    title = re.search(r"^# Case \S+ history — (.+)$", history, re.MULTILINE)
    attachments = [
        {"name": path.name, "text": attachment_text(path)}
        for path in sorted((folder / "attachments").glob("*"))
        if path.is_file()
    ]
    return {
        "id": "case-" + folder.name,
        "title": title[1].strip() if title else folder.name,
        "events": events,
        "attachments": attachments,
    }


def to_record(case: dict[str, Any], domain: str) -> DiscoveryRecord:
    id = case["id"]
    sources = [
        *(
            EvidenceText(
                id=f"{id}/event-{event['number']}",
                text=f"[{event['channel']}] {event['sender']} → {event['recipient']}\n{event['body']}",
                source="history.md",
                role="historical",
                speaker=event["sender"],
                timestamp=event["at"],
                origin="message",
            )
            for event in case["events"]
        ),
        *(
            EvidenceText(
                id=f"{id}/attachments/{item['name']}",
                text=item["text"],
                source="attachments",
                role="historical",
                origin="document",
            )
            for item in case["attachments"]
            if item["text"]
        ),
    ]
    return DiscoveryRecord(
        id=id, title=case["title"], kind="conversation", domain=domain, sources=sources
    )


def _hours(events: list[dict[str, str]]) -> float | None:
    try:
        start, end = (datetime.strptime(events[i]["at"], "%Y-%m-%d %H:%M:%S UTC") for i in (0, -1))
    except (IndexError, KeyError, ValueError):
        return None
    return (end - start).total_seconds() / 3600


def _counts(values: Counter[str], label: str) -> list[dict[str, Any]]:
    return [{label: key, "count": count} for key, count in values.most_common()]


def load(ctx: AnalysisContext) -> list[dict[str, Any]]:
    folders = sorted(path for path in ctx.data.iterdir() if (path / "history.md").is_file())
    if not folders:
        raise ValueError("Expected a track directory containing NNN/history.md case folders")
    files = sorted(path for folder in folders for path in folder.rglob("*") if path.is_file())
    return list(
        ctx.cached("dwelly-cases", {}, lambda: [read_case(f) for f in folders], files=files)
    )


async def build(ctx: AnalysisContext) -> Report:
    track = ctx.data.name
    cases = load(ctx)
    events = [event for case in cases for event in case["events"]]
    attachments = [item for case in cases for item in case["attachments"]]
    unreadable = [item["name"] for item in attachments if not item["text"]]
    report = Report(title=track, subtitle="Dwelly case histories · opening request to last event")
    report.metrics(
        {
            "Cases": len(cases),
            "History events": len(events),
            "Attachments": len(attachments),
            "Attachments without text": len(unreadable),
        }
    )
    report.chart(
        "Which channels carry the work?",
        ranking(
            _counts(Counter(e["channel"] for e in events), "channel"), "channel", unit="Events"
        ),
        caption=f"All {len(events)} history events",
    )
    report.chart(
        "How long are case histories?",
        ranking(
            [
                {"events": str(n), "count": count}
                for n, count in sorted(Counter(len(c["events"]) for c in cases).items())
            ],
            "events",
            unit="Cases",
        ),
        caption="History events per case",
    )
    report.chart(
        "What evidence is attached?",
        ranking(
            _counts(Counter(Path(i["name"]).suffix or "none" for i in attachments), "type"),
            "type",
            unit="Files",
        ),
        caption=f"{sum(bool(c['attachments']) for c in cases)} of {len(cases)} cases have attachments",
    )
    report.table(
        "Cases",
        [
            {
                "id": case["id"],
                "title": case["title"],
                "events": len(case["events"]),
                "channels": ", ".join(sorted({e["channel"] for e in case["events"]})),
                "attachments": ", ".join(item["name"] for item in case["attachments"]),
                "hours_open": round(hours, 1)
                if (hours := _hours(case["events"])) is not None
                else None,
            }
            for case in cases
        ],
        collapsed=True,
    )
    report.text(
        "Discovery scope",
        "Each case is one conversation record built from history.md alone: every event with "
        "channel, sender, recipient and time, plus readable attachment text. index.md is not read."
        + (
            f" Attachments without extractable text: {', '.join(unreadable)}." if unreadable else ""
        ),
    )
    domain = re.sub(r"[^a-z]+", "_", track.lower()).strip("_")
    await requested_discovery(
        report,
        ctx,
        [to_record(case, domain) for case in cases],
        scope=f"{track}: all {len(cases)} case histories",
        tools=[],
    )
    return report
