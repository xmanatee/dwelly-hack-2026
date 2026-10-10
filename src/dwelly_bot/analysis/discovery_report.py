"""Visual discovery views: topics, exceptional sources, quality review and policy drafts."""

from collections import Counter, defaultdict

from dwelly_bot.analysis.charts import matrix, ranking
from dwelly_bot.analysis.discovery_types import DiscoveryRecord
from dwelly_bot.contracts import JsonRecord
from dwelly_bot.reporting.models import Report
from dwelly_bot.reporting.theme import PALETTE


def add_discovery_views(
    report: Report, records: list[DiscoveryRecord], result: JsonRecord, *, scope: str
) -> None:
    screens = result["screens"]
    aliases: dict[str, set[str]] = defaultdict(set)
    for intent in result["taxonomy"]["intents"]:
        for alias in intent["aliases"]:
            aliases[alias].add(intent["id"])
    names = {intent["id"]: intent["name"] for intent in result["taxonomy"]["intents"]}
    details: dict[str, JsonRecord] = {}
    sampled = {row["id"]: row["reasons"] for row in result["review_sample"]}
    for record in records:
        row = screens.get(record.id)
        findings = row["findings"] if row else []
        details[record.id] = {
            "id": record.id,
            "title": record.title,
            "text": record.text(),
            "sources": [source.model_dump() for source in record.sources],
            "summary": row["summary"] if row else "Not screened",
            "fields": {
                "Source type": record.kind,
                "Topic": ", ".join(names[id] for id in sorted(aliases.get(row["topic"], set())))
                or row["topic"]
                if row
                else "Unknown",
                "Goal": row["goal"] if row else None,
                "Reported outcome": row["outcome"] if row else "Unknown",
            },
            "flags": [f["category"] for f in findings],
            "findings": findings,
            "insights": result["deep_extractions"].get(record.id),
            "sampling_reasons": sampled.get(record.id, []),
            "screening": row,
        }
    with_issues = [row for row in screens.values() if row["findings"]]
    support = [
        row
        for row in screens.values()
        if any(
            f["category"] == "support_need" and f["scope"] == "observed_case"
            for f in row["findings"]
        )
    ]
    report.metrics(
        {
            "Semantically screened": f"{len(screens)} / {len(records)}",
            "Candidate topics": len(names) or len({r["topic"] for r in screens.values()}),
            "Records to review": len(with_issues),
            "Cross-source concerns": len(result["conflicts"]["conflicts"]),
            "Quality-audited": len(result["audits"]["records"]),
            "Observed conversations": sum(r.kind == "conversation" for r in records),
        }
    )

    def labels_for(label: str) -> set[str]:
        return (
            {names[id] for id in aliases[label]}
            if aliases.get(label)
            else {"Needs taxonomy review" if names else label}
        )

    counts = Counter(
        topic
        for row in screens.values()
        for topic in set().union(
            *(labels_for(label) for label in [row["topic"], *row["secondary_topics"]])
        )
    )
    if counts:
        report.chart(
            "What operational topics recur?",
            ranking(
                [{"topic": topic, "count": count} for topic, count in counts.most_common(12)],
                "topic",
                unit="Screened records",
            ),
            caption=scope + f" · {min(12, len(counts))} / {len(counts)} topics · multi-label",
            note="Draft model assignments with cited sources. Counts describe only the successfully screened population; no extrapolation from a targeted review sample.",
        )
    cluster_topics: dict[str, Counter[str]] = defaultdict(Counter)
    for point in result["geometry"]["assignments"]:
        if point["cluster"] >= 0 and point["id"] in screens:
            cluster_topics[str(point["cluster"])][screens[point["id"]]["topic"]] += 1
    add_semantic_map(
        report,
        result["geometry"],
        details,
        labels={cluster: topics.most_common(1)[0][0] for cluster, topics in cluster_topics.items()},
    )
    finding_counts = Counter(f["category"] for row in screens.values() for f in row["findings"])
    if finding_counts:
        report.chart(
            "What could break the normal workflow?",
            ranking(
                [
                    {"issue": key.replace("_", " "), "count": count}
                    for key, count in finding_counts.most_common()
                ],
                "issue",
                unit="Candidate findings",
            ),
            caption="Evidence-backed candidates · pending review",
        )
        crosses = Counter(
            (
                ", ".join(names[id] for id in sorted(aliases.get(row["topic"], set())))
                or row["topic"],
                f["category"],
            )
            for row in screens.values()
            for f in row["findings"]
        )
        report.chart(
            "Which topics contain the exceptions?",
            matrix(
                [
                    {"topic": t, "issue": f.replace("_", " "), "count": n}
                    for (t, f), n in crosses.items()
                ],
                "topic",
                "issue",
                "count",
                unit="Findings",
                fill=0,
            ),
            width="full",
            caption="One record may contain several findings",
        )
        report.records(
            "Cases that need a closer look",
            [details[row["id"]] for row in with_issues],
            caption=scope,
        )
    if any(r.kind == "conversation" for r in records):
        report.records(
            "Explicitly disclosed support needs",
            [details[row["id"]] for row in support],
            caption=f"{len(support)} observed conversations flagged for review",
            note="Supported disclosures/stated needs only. No inference from demographics, style or mood; policy examples are excluded.",
        )
    if result["conflicts"]["conflicts"]:
        conflicts = [
            {
                "title": row["description"],
                "fields": {"Status": row["status"], "Next check": row["next_check"]},
                "findings": [
                    {
                        "category": "contradiction",
                        "description": row["description"],
                        "evidence": row["evidence"],
                    }
                ],
                "sources": [
                    source for id in row["record_ids"] for source in details[id]["sources"]
                ],
            }
            for row in result["conflicts"]["conflicts"]
        ]
        report.records(
            "Similar sources that disagree",
            conflicts,
            caption="Potential conflicts and scope differences",
        )
    reviews = result["audits"]["records"]
    if reviews:
        review_counts = Counter(row["decision"] for row in reviews)
        report.chart(
            "What did the independent review find?",
            ranking(
                [{"decision": k.replace("_", " "), "count": v} for k, v in review_counts.items()],
                "decision",
                unit="Audited records",
            ),
            caption=f"{len(reviews)} random flagged/unflagged records",
            note="A separate model review pass, not labelled ground truth. Disagreements/missed candidates require review; precision and recall remain unmeasured.",
        )
        report.records(
            "Audit disagreements",
            [
                {
                    **details[row["id"]],
                    "audit": row,
                    "findings": [row["issue"]] if row["issue"] else [],
                    "flags": [row["decision"]],
                }
                for row in reviews
                if row["decision"] != "supported"
            ],
        )
    for draft in result["procedure_drafts"]:
        report.flow(
            "Draft · " + names.get(draft["intent_id"], draft["intent_id"]),
            draft["steps"],
            note="Policy-grounded proposal, not an approved/executable skill. Stops: "
            + "; ".join(draft["stop_conditions"]),
        )
    if result["observed_patterns"]["patterns"]:
        report.records(
            "Repeated handling and negative paths",
            [
                {
                    "title": names.get(row["intent_id"], row["intent_id"]),
                    "fields": {"Cases": len(row["case_ids"]), "Status": row["status"]},
                    "pattern": row,
                }
                for row in result["observed_patterns"]["patterns"]
            ],
        )
    report.table("Draft taxonomy", result["taxonomy"]["intents"], collapsed=True)
    report.table(
        "Unmapped topic aliases",
        [{"label": label} for label in result["taxonomy"].get("unmapped_aliases", [])],
        collapsed=True,
    )
    report.table("Review selection", result["review_sample"], collapsed=True)
    report.table("Stage failures", result["errors"], collapsed=True)
    report.table("Semantic assignments", result["geometry"]["assignments"], collapsed=True)


def add_semantic_map(
    report: Report,
    geometry: JsonRecord,
    details: dict[str, JsonRecord],
    *,
    labels: dict[str, str] | None = None,
) -> None:
    """Clickable source map shared by lightweight exploration and deep discovery."""
    from plotly import graph_objects as go

    points: dict[str, list[JsonRecord]] = defaultdict(list)
    for point in geometry["assignments"]:
        points[str(point["cluster"])].append(point)
    fig = go.Figure()
    for index, (cluster, rows) in enumerate(points.items()):
        label = "Unassigned" if cluster == "-1" else "Group " + cluster
        label = (labels or {}).get(cluster, label)
        fig.add_scatter(
            x=[p["projection_x"] for p in rows],
            y=[p["projection_y"] for p in rows],
            mode="markers",
            name=label,
            customdata=[p["id"] for p in rows],
            text=[details[p["id"]]["title"] for p in rows],
            marker={
                "size": 8,
                "color": "#aeb6b0" if cluster == "-1" else PALETTE[index % len(PALETTE)],
            },
            hovertemplate="%{text}<extra></extra>",
        )
    fig.update_layout(
        xaxis={"title": "Projection 1", "showticklabels": False},
        yaxis={"title": "Projection 2", "showticklabels": False},
        legend={"font": {"size": 10}},
        height=430,
    )
    report.chart(
        "Which sources are similar or isolated?",
        fig,
        caption=geometry["embedding_model"],
        details=details,
        note="Density groups use full-dimensional normalized vectors. The PCA picture is for navigation, not risk, confidence or correctness. Grey points remain unassigned.",
    )
