"""Supplied case folders -> Planner input. No labels, outcomes or index files are loaded."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from dwelly_bot.contracts import RunConfig
from dwelly_bot.planner import PlanInput
from dwelly_bot.planner.context import parse_events
from dwelly_bot.planner.contracts import PlanDocument
from dwelly_bot.storage import file_hash
from hackathon_winner.export import CASE

TASK = (
    "Use the supplied context to plan the next supported response and concrete proposed actions. "
    "All available evidence is already supplied; no solver tools or bank execution are connected. "
    "Keep observed history separate from proposed future operations. Decide the concrete next "
    "actions, including a specific evidence request or handoff for a material gap. "
    "State missing information and what must not be claimed; do not append hypothetical future decisions."
)


@dataclass
class HistoryCase:
    case_id: str
    number: str
    history: str
    source: PlanInput
    input_files: dict[str, str]


def checked_path(path: Path, folder: Path) -> Path:
    if not path.resolve().is_relative_to(folder.resolve()):
        raise ValueError(f"Evidence path escapes its case folder: {path.name}")
    return path


def attachment_text(path: Path) -> str:
    if path.suffix.lower() in {".md", ".txt", ".csv", ".json"}:
        return path.read_text(encoding="utf-8")
    if path.suffix.lower() == ".pdf":
        try:
            from pypdf import PdfReader
        except ImportError:
            return "[Attachment unread: PDF reader unavailable; install the evaluation extra.]"
        try:
            content = "\n".join(page.extract_text() or "" for page in PdfReader(path).pages)
        except Exception as exc:
            return f"[Attachment unread: PDF extraction failed ({type(exc).__name__}).]"
        return content if content.strip() else "[Attachment unread: no PDF text layer; OCR needed.]"
    return f"[Attachment unread: unsupported {path.suffix or 'binary'} format; no OCR performed.]"


def load(
    track: Path, config: RunConfig, *, ids: list[str] | None = None, prefix: str = "banking"
) -> list[HistoryCase]:
    """Load history.md, context.md or request.md plus supplied attachments per case.

    The folder runner uses prefix='' to preserve organizer folder IDs verbatim. These are
    supplied snapshots, not a generated cutoff: the caller owns the evaluation input boundary.
    """
    folders = sorted(p for p in track.iterdir() if p.is_dir() and not p.name.startswith("."))

    def identity(path: Path) -> str:
        return f"{prefix}-{path.name}" if prefix else path.name

    if ids is not None:
        wanted = set(ids)
        folders = [p for p in folders if identity(p) in wanted]
        if missing := wanted - {identity(p) for p in folders}:
            raise ValueError(f"Unknown case IDs: {sorted(missing)}")
    if not folders:
        raise ValueError(f"No history.md/context.md cases found in {track}")
    cases = []
    for folder in folders:
        checked_path(folder, track)
        case_id = identity(folder)
        if not CASE.fullmatch(case_id) or case_id.casefold() in {
            "journals",
            "predictions.json",
            "report.html",
            "readme.md",
        }:
            raise ValueError(f"Unsafe or reserved case identifier {case_id!r}")
        main = next(
            (
                folder / n
                for n in ("history.md", "context.md", "request.md")
                if (folder / n).is_file()
            ),
            None,
        )
        if main is None:
            raise ValueError(f"{folder.name}: expected history.md, context.md or request.md")
        history = checked_path(main, folder).read_text(encoding="utf-8")
        if not history.strip():
            raise ValueError(f"{folder.name}: empty {main.name}")
        events = parse_events(history)
        # The latest requester message identifies the current issue; history is retained in full.
        customer = next(
            (e for e in reversed(events) if not e.sender.lower().startswith(("h&v", "harrow"))),
            None,
        )
        documents = [] if events else [PlanDocument(name=main.name, text=history)]
        inventory = {main.name: file_hash(main)}
        context = f"# Supplied case {folder.name}\n\n## {main.name}\n\n{history}"
        paths = sorted(p for p in (folder / "attachments").rglob("*") if p.is_file())
        if main.name != "request.md" and (folder / "request.md").is_file():
            paths.insert(0, folder / "request.md")
        for path in paths:
            checked_path(path, folder)
            name = path.relative_to(folder).as_posix()
            content = attachment_text(path)
            documents.append(PlanDocument(name=name, text=content))
            inventory[name] = file_hash(path)
            context += f"\n\n## {name}\n\n{content}"
        source = PlanInput(
            case_id=case_id,
            decision_time=events[-1].at if events else "Not supplied",
            request=customer.text if customer else history,
            task=TASK,
            events=events,
            documents=documents,
            datapoints={"input_files": inventory, "execution": "proposals only"},
            solver_tools=[],
        )
        cases.append(HistoryCase(case_id, folder.name, context, source, inventory))
    return cases
