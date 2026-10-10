"""Write docs/CATALOG.md from a built corpus: python -m synth.catalog out"""

import collections
import json
import sqlite3
import sys
from pathlib import Path


def main():
    out = Path(sys.argv[1] if len(sys.argv) > 1 else "out")
    con = sqlite3.connect(out / "banking_synth.sqlite")
    rows = con.execute(
        "SELECT c.family, c.scenario, c.variant, c.difficulty, l.expected_path, l.first_action_type, "
        "l.decision_after_event, l.edge_tags, MIN(c.case_number) FROM cases c JOIN case_labels l USING(case_key) "
        "GROUP BY c.scenario, c.variant ORDER BY c.family, c.scenario, c.variant").fetchall()
    fam = collections.defaultdict(list)
    for r in rows:
        fam[r[0]].append(r)
    lines = ["# Scenario catalogue", "",
             f"{len({r[1] for r in rows})} scenarios, {len(rows)} variants, {con.execute('SELECT COUNT(*) FROM cases').fetchone()[0]} cases in this build.",
             "Example = first case number generated for that variant.", ""]
    tags = collections.Counter(t for r in rows for t in json.loads(r[7]))
    lines += ["## Edge tags", "", ", ".join(f"`{t}` ({n})" for t, n in tags.most_common()), ""]
    for f in sorted(fam):
        lines += [f"## {f}", "", "| Scenario | Variant | Difficulty | Expected path | First action | Decide after | Tags | Example |",
                  "|---|---|---|---|---|---|---|---|"]
        for _, s, v, d, p, fa, da, t, ex in fam[f]:
            lines.append(f"| {s} | {v} | {d} | {p} | {fa} | {da} | {', '.join(json.loads(t))} | {ex} |")
        lines.append("")
    Path("docs").mkdir(exist_ok=True)
    Path("docs/CATALOG.md").write_text("\n".join(lines))
    print(f"docs/CATALOG.md: {len(rows)} variants")


if __name__ == "__main__":
    main()
