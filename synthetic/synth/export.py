"""Write the corpus: SQLite database, public-format case folders, blind snapshots, JSONL."""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import sqlite3
from pathlib import Path

from . import pools
from .core import CaseBuilder, World, long_date, to_json, ts

TRACK_DIR = "Banking & Financial Services"


# ---------------------------------------------------------------------------
# Markdown in the organiser's public format
# ---------------------------------------------------------------------------

def _event_md(i: int, e) -> str:
    att = ""
    if e.attachments:
        links = ", ".join(f"[{a}](attachments/{a})" for a in e.attachments)
        att = f"\n\nAttachments: {links}"
    return (f'<a id="event-{i:03d}"></a>\n## {ts(e.at)} UTC — event {i:03d}\n\n'
            f"- **Channel:** {e.channel}\n- **From:** {e.sender}\n- **To:** {e.recipient}\n\n{e.body}{att}\n")


def history_md(b: CaseBuilder, upto: int | None = None) -> str:
    evs = b.events if upto is None else b.events[:upto]
    head = f"# Case {b.case_number} history — {b.meta_fields['title']}\n\nTotal events: {len(evs)}\n\n"
    return head + "\n".join(_event_md(i, e) for i, e in enumerate(evs, 1))


def index_md(b: CaseBuilder, blind: bool = False) -> str:
    m = b.meta_fields
    first, last = b.events[0].at, b.events[-1].at
    da = b.labels["decision_after_event"]
    lines = [f"# Case {b.case_number}: {m['title'] if not blind else 'Untitled request'}", "", "## Case details", "",
             f"- **Source role:** {m['source_role']}"]
    if blind:
        lines.append("- **Status:** Open")
    else:
        lines.append(f"- **Status:** {m['status_line']}")
    lines.append(f"- **Bank:** {b.bank_name} (fictional)")
    for k, v in b.extra_details:
        lines.append(f"- **{k}:** {v}")
    lines.append(f"- **Created:** {ts(first)} UTC")
    if blind:
        lines.append(f"- **Updated:** {ts(b.events[da - 1].at)} UTC")
    else:
        lines += [f"- **Updated:** {ts(last)} UTC", f"- **Completed:** {ts(last)} UTC"]
    lines += ["", "## Initial request", "", m["initial_request"], ""]
    if not blind:
        lines += ["## Overview", "", m["overview"], "", "## Next action at escalation", "", m["next_action"], "",
                  "## Outcome", "", m["outcome"], ""]
    lines += ["## History", "", "[Read the complete event history](history.md).", "", "## Attachments", ""]
    atts = [a for a in b.attachments if (not blind or a.first_event <= da)]
    if atts:
        lines += [f"- [{a.filename}](attachments/{a.filename})" for a in atts]
    else:
        lines.append("None.")
    return "\n".join(lines) + "\n"


def write_case_folder(b: CaseBuilder, root: Path, blind: bool):
    d = root / b.case_number
    d.mkdir(parents=True, exist_ok=True)
    da = b.labels["decision_after_event"]
    (d / "index.md").write_text(index_md(b, blind), encoding="utf-8")
    (d / "history.md").write_text(history_md(b, da if blind else None), encoding="utf-8")
    atts = [a for a in b.attachments if (not blind or a.first_event <= da)]
    if atts:
        (d / "attachments").mkdir(exist_ok=True)
        for a in atts:
            (d / "attachments" / a.filename).write_bytes(a.data)


# ---------------------------------------------------------------------------
# SQLite
# ---------------------------------------------------------------------------

def _insert(con: sqlite3.Connection, table: str, rows: list[dict]):
    if not rows:
        return
    cols = [r[1] for r in con.execute(f"PRAGMA table_info({table})")]
    for r in rows:
        unknown = set(r) - set(cols)
        if unknown:
            raise ValueError(f"{table}: unknown columns {unknown}")
        keys = list(r)
        con.execute(f"INSERT INTO {table} ({','.join(keys)}) VALUES ({','.join('?' * len(keys))})",
                    [r[k] for k in keys])


TABLE_ORDER = ["banks", "systems", "customers", "businesses", "business_users", "business_user_roles",
               "third_party_authorities", "vulnerability_notes", "accounts", "account_holders", "payees",
               "transactions", "transfers", "payment_recalls", "incoming_payments", "standing_orders",
               "standing_order_runs", "dd_mandates", "dd_collections", "dd_indemnity_claims", "cards",
               "card_dispatches", "card_authorisations", "card_disputes", "devices", "sign_in_events",
               "access_status", "profile_change_requests", "security_reports", "fees", "documents",
               "payment_batches", "batch_lines", "batch_approvals", "access_requests", "limit_change_requests",
               "acquiring_reports", "complaints", "service_cases", "data_requests"]


def write_db(world: World, path: Path):
    if path.exists():
        path.unlink()
    con = sqlite3.connect(path)
    con.executescript((Path(__file__).parent / "schema.sql").read_text())
    _insert(con, "banks", [dict(bank_id=i, name=n, short_name=s, sort_code_prefix=p, is_home_bank=1)
                           for i, n, s, p, _ in pools.HOME_BANKS])
    _insert(con, "systems", [dict(system_id=i, display_name=l, kind=k, read_only=ro, description=desc)
                             for i, l, k, ro, desc in pools.SYSTEMS])
    unknown = set(world.rows) - set(TABLE_ORDER)
    if unknown:
        raise ValueError(f"rows for unknown tables {unknown}")
    for t in TABLE_ORDER:
        _insert(con, t, world.rows.get(t, []))
    for b in world.cases:
        m, L = b.meta_fields, b.labels
        _insert(con, "cases", [dict(
            case_key=b.case_key, case_number=b.case_number, scenario=b.sdef.name, family=b.sdef.family,
            variant=b.variant, title=m["title"], source_role=m["source_role"], status_line=m["status_line"],
            bank_id=b.bank["bank_id"], customer_id=b.customer_id, business_id=b.business_id,
            created_at=ts(b.events[0].at), updated_at=ts(b.events[-1].at), completed_at=ts(b.events[-1].at),
            initial_request=m["initial_request"], overview=m["overview"], next_action=m["next_action"],
            outcome=m["outcome"], difficulty=b.difficulty)])
        _insert(con, "case_events", [dict(
            case_key=b.case_key, seq=i, at=ts(e.at), channel=e.channel, sender=e.sender, recipient=e.recipient,
            body=e.body, authenticated=e.authenticated, actor_kind=e.actor,
            is_decision_visible=int(i <= L["decision_after_event"])) for i, e in enumerate(b.events, 1)])
        _insert(con, "case_attachments", [dict(
            case_key=b.case_key, filename=a.filename, media_type=a.media_type, first_event_seq=a.first_event,
            description=a.description, contains_untrusted_instructions=int(a.untrusted),
            sha256=hashlib.sha256(a.data).hexdigest()) for a in b.attachments])
        _insert(con, "case_labels", [dict(case_key=b.case_key, **{
            k: (to_json(v) if isinstance(v, list) else v) for k, v in L.items()})])
        _insert(con, "case_system_responses", [dict(case_key=b.case_key, system_id=r["system_id"],
                                                    query_hint=r["query_hint"], response_text=r["response_text"],
                                                    fields_available=to_json(r["fields_available"]),
                                                    fields_absent=to_json(r["fields_absent"]))
                                               for r in b.system_responses])
        _insert(con, "case_records", [dict(case_key=b.case_key, table_name=t, record_id=r)
                                      for t, r in sorted(b.records)])
    con.commit()
    con.close()


# ---------------------------------------------------------------------------
# JSONL + top-level writer
# ---------------------------------------------------------------------------

def case_json(b: CaseBuilder) -> dict:
    return dict(
        case_key=b.case_key, case_number=b.case_number, scenario=b.sdef.name, family=b.sdef.family,
        variant=b.variant, difficulty=b.difficulty, bank=b.bank["name"], **b.meta_fields,
        events=[dict(seq=i, at=ts(e.at), channel=e.channel, sender=e.sender, recipient=e.recipient,
                     body=e.body, authenticated=e.authenticated, actor=e.actor, attachments=e.attachments)
                for i, e in enumerate(b.events, 1)],
        attachments=[dict(filename=a.filename, media_type=a.media_type, first_event=a.first_event,
                          description=a.description, untrusted=a.untrusted) for a in b.attachments],
        labels=b.labels, system_responses=b.system_responses,
        records=[dict(table=t, id=r) for t, r in sorted(b.records)],
    )


def write_all(world: World, out: Path):
    for sub in ("cases", "cases_blind"):
        if (out / sub).exists():
            shutil.rmtree(out / sub, ignore_errors=True)
            shutil.rmtree(out / sub)  # second pass clears anything the first left behind
    out.mkdir(parents=True, exist_ok=True)
    full = out / "cases" / TRACK_DIR
    blind = out / "cases_blind" / TRACK_DIR
    for b in world.cases:
        write_case_folder(b, full, blind=False)
        write_case_folder(b, blind, blind=True)
    write_db(world, out / "banking_synth.sqlite")
    with open(out / "cases.jsonl", "w", encoding="utf-8") as f:
        for b in world.cases:
            f.write(json.dumps(case_json(b), ensure_ascii=False) + "\n")
