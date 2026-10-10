"""Integrity + format checks on a built corpus.

python -m synth.validate out
"""

from __future__ import annotations

import json
import re
import sqlite3
import sys
from pathlib import Path

from .export import TRACK_DIR

EVENT_RE = re.compile(
    r'<a id="event-(\d{3})"></a>\n## (\d{4}-\d\d-\d\d \d\d:\d\d:\d\d) UTC — event (\d{3})\n\n'
    r"- \*\*Channel:\*\* (.+)\n- \*\*From:\*\* (.+)\n- \*\*To:\*\* (.+)\n\n", re.M)
INDEX_SECTIONS = ["Case details", "Initial request", "Overview", "Next action at escalation", "Outcome", "History",
                  "Attachments"]


def check(out: Path) -> list[str]:
    errs: list[str] = []
    con = sqlite3.connect(out / "banking_synth.sqlite")
    con.execute("PRAGMA foreign_keys=ON")
    for row in con.execute("PRAGMA foreign_key_check"):
        errs.append(f"foreign key violation: {row}")

    # every case_records reference resolves
    pk = {}
    for (t,) in con.execute("SELECT DISTINCT table_name FROM case_records"):
        col = [r[1] for r in con.execute(f"PRAGMA table_info({t})") if r[5] == 1]
        pk[t] = col[0] if len(col) == 1 else None
    for t, rid, ck in con.execute("SELECT table_name, record_id, case_key FROM case_records"):
        if pk.get(t) and not con.execute(f"SELECT 1 FROM {t} WHERE {pk[t]}=?", (rid,)).fetchone():
            errs.append(f"{ck}: dangling record {t}/{rid}")

    for ck, n, da in con.execute("SELECT c.case_key, (SELECT COUNT(*) FROM case_events e WHERE e.case_key=c.case_key), "
                                 "l.decision_after_event FROM cases c JOIN case_labels l USING(case_key)"):
        if not (1 <= da < n):
            errs.append(f"{ck}: decision_after_event {da} with {n} events")
    for ck, seq, prev, cur in con.execute(
            "SELECT case_key, seq, LAG(at) OVER (PARTITION BY case_key ORDER BY seq), at FROM case_events"):
        if prev and cur < prev:
            errs.append(f"{ck}: event {seq} earlier than previous")

    # markdown format parity with organiser files
    for d in sorted((out / "cases" / TRACK_DIR).iterdir()):
        idx = (d / "index.md").read_text()
        hist = (d / "history.md").read_text()
        secs = re.findall(r"^## (.+)$", idx, re.M)
        if secs != INDEX_SECTIONS:
            errs.append(f"{d.name}: index sections {secs}")
        evs = EVENT_RE.findall(hist)
        total = int(re.search(r"Total events: (\d+)", hist).group(1))
        if len(evs) != total:
            errs.append(f"{d.name}: parsed {len(evs)} events, header says {total}")
        for a, _, b2, *_ in evs:
            if a != b2:
                errs.append(f"{d.name}: anchor/event mismatch {a}/{b2}")
        for link in re.findall(r"\(attachments/([^)]+)\)", idx + hist):
            if not (d / "attachments" / link).exists():
                errs.append(f"{d.name}: missing attachment {link}")

    # blind snapshots must not leak later events or outcome sections
    for d in sorted((out / "cases_blind" / TRACK_DIR).iterdir()):
        idx = (d / "index.md").read_text()
        if "## Outcome" in idx or "## Overview" in idx or "Next action" in idx:
            errs.append(f"blind {d.name}: outcome section present")
        ck = f"SYN-{d.name}"
        da = con.execute("SELECT decision_after_event FROM case_labels WHERE case_key=?", (ck,)).fetchone()[0]
        n = len(EVENT_RE.findall((d / "history.md").read_text()))
        if n != da:
            errs.append(f"blind {d.name}: {n} events visible, expected {da}")

    # labels well-formed
    for ck, *js in con.execute("SELECT case_key, required_gates, must_not, must_convey, not_established, signposts, "
                               "edge_tags FROM case_labels"):
        for j in js:
            if not isinstance(json.loads(j), list):
                errs.append(f"{ck}: label field not a list")
    for (ck,) in con.execute("SELECT case_key FROM case_labels WHERE case_key NOT IN (SELECT case_key FROM case_system_responses) "
            "AND expected_path NOT IN ('redirect_to_secure_route','decline_and_signpost','no_action_explain')"):
        errs.append(f"{ck}: no system responses recorded")
    con.close()
    return errs


def main():
    out = Path(sys.argv[1] if len(sys.argv) > 1 else "out")
    errs = check(out)
    for e in errs[:200]:
        print(e)
    print(f"{len(errs)} problem(s)")
    sys.exit(1 if errs else 0)


if __name__ == "__main__":
    main()
