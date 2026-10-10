"""Offline projection of the supplied generator output; never imported by runtime sources."""

from __future__ import annotations

import re
import shutil
import sqlite3
import tempfile
from contextlib import closing
from datetime import UTC, datetime
from pathlib import Path

from dwelly_bot.adapters.synthetic_banking.policy import is_observation
from dwelly_bot.channels.intake import inbound_adapter
from dwelly_bot.storage import file_hash, save_json


def timestamp(value: str) -> str:
    parsed = datetime.fromisoformat(value)
    return (parsed if parsed.tzinfo else parsed.replace(tzinfo=UTC)).astimezone(UTC).isoformat()


def document_text(path: Path, media_type: str) -> tuple[str | None, str]:
    if media_type in {"text/plain", "text/csv"}:
        return path.read_text(encoding="utf-8"), "text"
    if media_type == "application/pdf":
        from pypdf import PdfReader

        text = "\n".join(page.extract_text() or "" for page in PdfReader(path).pages)
        return (text, "pdf_text") if text.strip() else (None, "no_text_layer")
    return None, "unsupported_media"


def prepare(original: Path, output: Path) -> dict[str, object]:
    """Keep labels/full histories separate; build runtime state and one trigger per case.

    The source entity tables are END state. Their copies are for inspection only;
    runtime reads the generator's decision-point system responses instead.
    """
    if output.exists():
        raise FileExistsError(f"Dataset directory exists: {output}")
    if output.resolve().is_relative_to(original.resolve()):
        raise ValueError("Dataset output must be outside the original corpus")
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=".bank-prepare-", dir=output.parent) as temporary:
        staged = Path(temporary) / "dataset"
        manifest = _prepare(original, staged)
        if output.exists():
            raise FileExistsError(f"Dataset directory exists: {output}")
        staged.rename(output)
    return manifest


def _prepare(original: Path, output: Path) -> dict[str, object]:
    """Build in a temporary sibling; only a complete projection becomes visible."""
    source = original / "banking_synth.sqlite"
    output.mkdir(parents=True)
    state, cases, evaluation = (output / d for d in ("state", "cases", "evaluation"))
    for directory in (state, cases, evaluation):
        directory.mkdir()
    # Preserve every original byte, including attachments and generator metadata.
    shutil.copytree(original, evaluation / "original")
    shutil.copyfile(source, state / "end-state.sqlite")
    with closing(sqlite3.connect(state / "end-state.sqlite")) as end:
        for (name,) in end.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall():
            if name == "cases" or name.startswith("case_"):
                end.execute('DROP TABLE "' + name.replace('"', '""') + '"')
        end.commit()

    counts: dict[str, int] = {"cases": 0, "messages": 0, "responses": 0, "documents": 0}
    withheld_responses = 0
    media: dict[str, int] = {}
    with (
        closing(sqlite3.connect(source.resolve().as_uri() + "?mode=ro", uri=True)) as src,
        closing(sqlite3.connect(state / "decision.sqlite")) as dst,
    ):
        src.row_factory = sqlite3.Row
        dst.executescript(Path(__file__).with_name("schema.sql").read_text())
        dst.executemany(
            "INSERT INTO banks VALUES(?,?)", src.execute("SELECT bank_id,name FROM banks")
        )
        dst.executemany(
            "INSERT INTO systems VALUES(?,?)",
            src.execute("SELECT system_id,description FROM systems"),
        )
        for case in src.execute("SELECT case_key,case_number,bank_id FROM cases ORDER BY case_key"):
            key = case["case_key"]
            if not re.fullmatch(r"SYN-\d{4,}", key):
                raise ValueError(f"Invalid synthetic case ID: {key!r}")
            events = src.execute(
                "SELECT * FROM case_events WHERE case_key=? AND is_decision_visible=1 ORDER BY seq",
                (key,),
            ).fetchall()
            if not events:
                raise ValueError(f"No decision-time events for {key}")
            at = timestamp(events[-1]["at"])
            dst.execute("INSERT INTO snapshots VALUES(?,?,?)", (key, at, case["bank_id"]))
            incoming = [
                e for e in events if e["actor_kind"] in {"customer", "third_party", "external"}
            ]
            if not incoming:
                raise ValueError(f"No inbound request for {key}")
            request = incoming[-1]
            # Full contacts do not exist in the supplied corpus. These explicit local
            # aliases exercise routing/search, never authentication or real delivery.
            email = f"{key.lower()}@example.invalid"
            phone = f"+9992026{int(case['case_number']):06d}"
            dst.execute(
                "INSERT INTO contacts VALUES(?,?,?,?,?,?)",
                (key, f"contact-{key}", request["sender"], email, phone, request["actor_kind"]),
            )
            channel = request["channel"].casefold()
            transport = "call" if "call" in channel else "email" if channel == "email" else "ticket"
            event = {
                "event_id": f"{key}-event-{request['seq']}",
                "scope_id": key,
                "received_at": at,
                "channel": transport,
                "text": f"Source channel: {request['channel']}; actor: {request['actor_kind']}; "
                f"source authenticated flag: {request['authenticated']}.\n\n{request['body']}",
                "hints": {"name": request["sender"]},
            }
            if transport == "call":
                event.update(caller=phone, session_id=f"call-{key}", active=True)
            elif transport == "email":
                event.update(sender=email, thread_id=f"thread-{key}")
            else:
                event.update(ticket_id=key)
            parsed = inbound_adapter.validate_python(event)
            save_json(cases / f"{key}.json", parsed.model_dump(mode="json"))
            for e in events:
                dst.execute(
                    "INSERT INTO messages VALUES(?,?,?,?,?,?,?,?,?)",
                    (
                        key,
                        e["seq"],
                        timestamp(e["at"]),
                        e["channel"],
                        e["sender"],
                        e["recipient"],
                        e["body"],
                        e["authenticated"],
                        e["actor_kind"],
                    ),
                )
            responses = src.execute(
                "SELECT case_key,system_id,query_hint,response_text,fields_available,fields_absent "
                "FROM case_system_responses WHERE case_key=?",
                (key,),
            ).fetchall()
            readable = [r for r in responses if is_observation(r["system_id"], r["query_hint"])]
            withheld_responses += len(responses) - len(readable)
            dst.executemany("INSERT INTO responses VALUES(?,?,?,?,?,?)", readable)
            for attachment in src.execute(
                "SELECT a.*,e.at FROM case_attachments a JOIN case_events e "
                "ON a.case_key=e.case_key AND a.first_event_seq=e.seq "
                "WHERE a.case_key=? AND e.is_decision_visible=1",
                (key,),
            ):
                name = attachment["filename"]
                if Path(name).name != name or Path(case["case_number"]).name != case["case_number"]:
                    raise ValueError("Invalid source attachment path")
                path = (
                    original
                    / "cases"
                    / "Banking & Financial Services"
                    / case["case_number"]
                    / "attachments"
                    / name
                )
                digest = file_hash(path)
                if digest != attachment["sha256"]:
                    raise ValueError(f"Attachment hash mismatch: {key}/{name}")
                text, status = document_text(path, attachment["media_type"])
                target = state / "attachments" / key / name
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(path, target)
                dst.execute(
                    "INSERT INTO documents VALUES(?,?,?,?,?,?,?)",
                    (
                        key,
                        name,
                        timestamp(attachment["at"]),
                        attachment["media_type"],
                        digest,
                        text,
                        status,
                    ),
                )
                media[status] = media.get(status, 0) + 1
            counts["cases"] += 1
            counts["messages"] += len(events)
            counts["responses"] += len(readable)
        counts["documents"] = dst.execute("SELECT COUNT(*) FROM documents").fetchone()[0]
        dst.commit()
    manifest: dict[str, object] = {
        "format": "dwelly-synthetic-bank-v1",
        "source_sha256": file_hash(source),
        "runtime_sha256": file_hash(state / "decision.sqlite"),
        "cases_sha256": {p.name: file_hash(p) for p in sorted(cases.glob("*.json"))},
        "counts": counts,
        "document_extraction": media,
        "withheld_action_or_unreviewed_responses": withheld_responses,
        "read_query_policy_sha256": file_hash(Path(__file__).with_name("read_queries.json")),
        "contact_aliases": "Synthetic .invalid email and unassigned +999 phone; not source facts.",
        "boundary": "End-state entities and evaluator labels are excluded from decision.sqlite.",
    }
    save_json(output / "manifest.json", manifest)
    return manifest
