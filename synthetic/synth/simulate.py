"""Answer an agent's tool call from the database, the way a blind evaluation simulator would.

    from synth.simulate import Simulator
    sim = Simulator("out/banking_synth.sqlite")
    sim.visible("SYN-0001")                 # what the agent may see at the decision point
    sim.query("SYN-0001", "transfer_journal", ["status", "send timestamp"])

Only the case's recorded system responses are used. A requested field that the record does not
hold gets "No further data returned." - never an invented value.
"""

from __future__ import annotations

import json
import sqlite3

NO_DATA = "No further data returned."


class Simulator:
    def __init__(self, db_path: str):
        self.con = sqlite3.connect(db_path)
        self.con.row_factory = sqlite3.Row

    def visible(self, case_key: str) -> dict:
        c = self.con.execute("SELECT case_number, source_role, bank_id, initial_request FROM cases WHERE case_key=?",
                             (case_key,)).fetchone()
        da = self.con.execute("SELECT decision_after_event FROM case_labels WHERE case_key=?", (case_key,)).fetchone()[0]
        events = [dict(r) for r in self.con.execute(
            "SELECT seq, at, channel, sender, recipient, body, authenticated FROM case_events "
            "WHERE case_key=? AND seq<=? ORDER BY seq", (case_key, da))]
        atts = [dict(r) for r in self.con.execute(
            "SELECT filename, media_type FROM case_attachments WHERE case_key=? AND first_event_seq<=?", (case_key, da))]
        return dict(case=dict(c), events=events, attachments=atts)

    def systems_for(self, case_key: str) -> list[str]:
        return [r[0] for r in self.con.execute(
            "SELECT DISTINCT system_id FROM case_system_responses WHERE case_key=?", (case_key,))]

    def query(self, case_key: str, system_id: str, fields: list[str] | None = None) -> str:
        rows = self.con.execute("SELECT * FROM case_system_responses WHERE case_key=? AND system_id=?",
                                (case_key, system_id)).fetchall()
        if not rows:
            return NO_DATA
        parts = []
        for r in rows:
            parts.append(r["response_text"])
            absent = json.loads(r["fields_absent"])
            avail = [a.lower() for a in json.loads(r["fields_available"])]
            for f in fields or []:
                fl = f.lower()
                if any(fl in a or a in fl for a in absent) or not any(fl in a or a in fl for a in avail):
                    parts.append(f"{f}: {NO_DATA}")
        return "\n".join(dict.fromkeys(parts))

    def labels(self, case_key: str) -> dict:
        r = dict(self.con.execute("SELECT * FROM case_labels WHERE case_key=?", (case_key,)).fetchone())
        for k, v in r.items():
            if isinstance(v, str) and v.startswith("["):
                r[k] = json.loads(v)
        return r
