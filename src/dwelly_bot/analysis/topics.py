"""Composable topic exploration; no LLM labels, screening or mandatory workflow."""

from collections import Counter, defaultdict

from dwelly_bot.analysis.charts import ranking
from dwelly_bot.analysis.discovery_report import add_semantic_map
from dwelly_bot.analysis.discovery_types import DiscoveryRecord
from dwelly_bot.analysis.semantic import EmbeddingConfig, map_records
from dwelly_bot.analysis.session import AnalysisContext
from dwelly_bot.contracts import JsonRecord
from dwelly_bot.reporting.models import Report
from dwelly_bot.reporting.theme import DISPLAY


async def add_topics(
    report: Report,
    ctx: AnalysisContext,
    records: list[DiscoveryRecord],
    *,
    embedding: EmbeddingConfig | None = None,
    min_cluster_size: int = 4,
    keyword_stop_words: str | list[str] | None = None,
) -> JsonRecord:
    """Add group membership, clickable points and review queues; return reusable geometry."""
    from sklearn.feature_extraction.text import TfidfVectorizer

    geometry = await map_records(
        ctx, records, embedding=embedding, min_cluster_size=min_cluster_size
    )
    assignments = {row["id"]: row for row in geometry["assignments"]}
    grouped: dict[int, list[int]] = defaultdict(list)
    for index, record in enumerate(records):
        grouped[assignments[record.id]["cluster"]].append(index)
    vectorizer = TfidfVectorizer(
        max_features=8000, ngram_range=(1, 2), stop_words=keyword_stop_words
    )
    texts = [record.text() for record in records]
    # The recipe owns language choice; keyword filtering does not change the vectors.
    has_words = any(vectorizer.build_analyzer()(text) for text in texts)
    matrix = vectorizer.fit_transform(texts) if has_words else None
    labels = {"-1": "Unassigned"}
    for cluster, indices in grouped.items():
        if cluster >= 0:
            terms = ""
            if matrix is not None:
                weights = matrix[indices].mean(axis=0).A1
                terms = " · ".join(vectorizer.get_feature_names_out()[weights.argsort()[-3:][::-1]])
            labels[str(cluster)] = f"Group {cluster}" + (f" · {terms}" if terms else "")
    details = {
        record.id: {
            "id": record.id,
            "title": record.title,
            "text": record.text(),
            "sources": [source.model_dump() for source in record.sources],
            "fields": {
                "Group": labels[str(assignments[record.id]["cluster"])],
                "Nearest records": assignments[record.id]["nearest_ids"],
                "Neighbor distance": assignments[record.id]["neighbor_distance"],
            },
            "flags": ["Unassigned"] if assignments[record.id]["cluster"] == -1 else [],
        }
        for record in records
    }
    report.metrics(
        {
            "Mapped records": len(records),
            "Candidate groups": len(geometry["clusters"]),
            "Unassigned": len(grouped.get(-1, [])),
            "Repeated exact texts": sum(n - 1 for n in Counter(texts).values()),
        }
    )
    report.records(
        "Groups to review",
        [
            {
                "title": labels[str(row["cluster"])],
                "fields": {"Records": row["count"]},
                "representatives": [details[id] for id in row["representatives"]],
                "boundary_records": [details[id] for id in row["boundary_ids"]],
                "member_ids": [records[i].id for i in grouped[row["cluster"]]],
            }
            for row in geometry["clusters"]
        ],
        note="Keyword hints, not validated intent labels. Inspect representatives and boundary records.",
    )
    add_semantic_map(report, geometry, details, labels=labels)
    ranked = sorted(
        geometry["assignments"], key=lambda row: row["neighbor_distance"] or 0, reverse=True
    )
    isolation = ranking(
        [{"id": row["id"], "distance": row["neighbor_distance"] or 0} for row in ranked[:12]],
        "id",
        "distance",
        unit="Cosine distance",
        id_column="id",
    )
    isolation.update_traces(
        texttemplate=f"%{{text:.{DISPLAY['decimals']}f}}",
        hovertemplate=f"%{{y}}<br>%{{x:.{DISPLAY['decimals']}f}} cosine distance<extra></extra>",
    )
    report.chart(
        "Most isolated records",
        isolation,
        details=details,
        note="Distance from nearest neighbors is a review signal, not severity or an error verdict.",
    )
    report.records(
        "Unassigned records", [details[records[i].id] for i in grouped.get(-1, [])], collapsed=True
    )
    report.table(
        "Closest pairs",
        geometry["pairs"],
        collapsed=True,
        note="Candidate duplicates or related requests; compare amounts, dates and negation before merging.",
    )
    report.records("All mapped records", list(details.values()), collapsed=True)
    return geometry
