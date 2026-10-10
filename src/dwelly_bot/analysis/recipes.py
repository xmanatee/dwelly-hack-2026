"""Small deterministic recipes; domain meanings and loading stay in benchmark code."""

from __future__ import annotations

import math
import random
import re
import statistics
from collections import Counter, defaultdict
from collections.abc import Callable, Sequence
from functools import partial
from typing import Any

from dwelly_bot.analysis.data import Table
from dwelly_bot.analysis.session import AnalysisContext
from dwelly_bot.contracts import JsonRecord
from dwelly_bot.reporting.models import Report
from dwelly_bot.storage import fingerprint


def sample(rows: Sequence[JsonRecord], limit: int, seed: int = 0) -> list[JsonRecord]:
    if limit < 0:
        raise ValueError("Sample size cannot be negative")
    indices = sorted(random.Random(seed).sample(range(len(rows)), min(len(rows), limit)))
    return [rows[index] for index in indices]


def profile(table: Table) -> list[JsonRecord]:
    result: list[JsonRecord] = []
    for column in table.columns:
        values = [row.get(column) for row in table.rows]
        missing = sum(value is None or value == "" for value in values)
        present = [value for value in values if value is not None and value != ""]
        types = Counter(type(value).__name__ for value in present)
        result.append(
            {
                "table": table.name,
                "column": column,
                "rows": len(values),
                "missing": missing,
                "distinct": len(
                    {
                        (
                            type(value).__name__,
                            fingerprint(value) if isinstance(value, (list, dict)) else value,
                        )
                        for value in present
                    }
                ),
                "types": ", ".join(f"{name}: {count}" for name, count in types.most_common()),
            }
        )
    return result


def segments(table: Table, *dimensions: str) -> list[JsonRecord]:
    table.require(*dimensions)
    counts: Counter[tuple[str, ...]] = Counter(
        tuple(str(row.get(column, "<missing>")) for column in dimensions) for row in table.rows
    )
    return [
        {**dict(zip(dimensions, group, strict=True)), "count": count}
        for group, count in counts.most_common()
    ]


def _numbers(table: Table, column: str) -> tuple[list[float], int]:
    table.require(column)
    values = []
    for row in table.rows:
        try:
            value = float(row[column])
            if math.isfinite(value):
                values.append(value)
        except (ValueError, TypeError, KeyError):
            continue
    return sorted(values), len(table.rows) - len(values)


def numeric_summary(table: Table, column: str) -> JsonRecord:
    values, invalid = _numbers(table, column)
    return {
        "field": column,
        "valid": len(values),
        "invalid_or_missing": invalid,
        "min": values[0] if values else None,
        "median": statistics.median(values) if values else None,
        "p95": values[int((len(values) - 1) * 0.95)] if values else None,
        "max": values[-1] if values else None,
    }


def exceptions(table: Table, rules: dict[str, Callable[[JsonRecord], bool]]) -> list[JsonRecord]:
    """Independent flags; no automatic escalation, combined risk score or hidden filtering."""
    return [
        {"record_id": row.get(table.id_column) if table.id_column else index, "flags": flags}
        for index, row in enumerate(table.rows)
        if (flags := [name for name, rule in rules.items() if rule(row)])
    ]


def histogram(table: Table, column: str, *, bins: int = 30) -> Any:
    """Aggregate bins in Python so HTML does not embed an entire numerical corpus."""
    from plotly import graph_objects as go

    if bins < 1:
        raise ValueError("Histogram bins must be positive")
    values, invalid = _numbers(table, column)
    if not values:
        raise ValueError("Histogram requires at least one finite numeric observation")
    low, high = min(values), max(values)
    width = (high - low) / bins if high > low else 1.0
    counts = Counter(min(bins - 1, int((value - low) / width)) for value in values)
    return go.Figure(
        go.Bar(
            x=[low + (i + 0.5) * width for i in range(bins)],
            y=[counts[i] for i in range(bins)],
            width=width,
        ),
        layout={"title": f"{column}: {len(values)} valid; {invalid} missing or invalid"},
    )


def add_profile(
    report: Report,
    tables: list[Table],
    *,
    preview: int = 8,
    ctx: AnalysisContext | None = None,
) -> None:
    catalogue: list[JsonRecord] = []
    quality_rows: list[JsonRecord] = []
    previews: list[JsonRecord] = []
    id_checks: list[JsonRecord] = []
    for table in tables:
        catalogue.append(
            {
                "table": table.name,
                "rows": len(table.rows),
                "fields": len(table.columns),
                "role": table.role,
                "notes": table.notes,
            }
        )
        if table.id_column:
            table.require(table.id_column)
            ids = [row.get(table.id_column) for row in table.rows]
            id_checks.append(
                {
                    "table": table.name,
                    "id_column": table.id_column,
                    "duplicate_ids": len(ids) - len(set(ids)),
                    "missing_ids": sum(v is None or v == "" for v in ids),
                }
            )
        quality = (
            ctx.cached("profile/" + table.name, table.rows, partial(profile, table))
            if ctx
            else profile(table)
        )
        quality_rows.extend(quality)
        previews.append(
            {
                "title": table.name,
                "fields": {"Source rows": len(table.rows), "Fields": len(table.columns)},
                "sample_rows": table.rows[:preview],
                "column_profile": quality,
            }
        )
    report.table("Data catalogue", catalogue, collapsed=True)
    if id_checks:
        report.table("Identity checks", id_checks, collapsed=True)
    report.table("Field profiles", quality_rows, collapsed=True)
    report.records("Raw table samples", previews, collapsed=True)


def text_groups(table: Table, text: str, id_column: str, *, groups: int = 6) -> list[JsonRecord]:
    """Exploratory TF-IDF groups; IDs and distances are not intents or correctness scores."""
    from sklearn.cluster import KMeans
    from sklearn.feature_extraction.text import TfidfVectorizer

    table.require(text, id_column)
    records = [row for row in table.rows if str(row.get(text, "")).strip()]
    if groups < 1 or len(records) < 3:
        raise ValueError("Text grouping requires positive groups and at least three text records")
    vectorizer = TfidfVectorizer(max_features=5000, stop_words="english", min_df=1)
    vectors = vectorizer.fit_transform([str(row[text]) for row in records])
    count = min(groups, len(records), len({str(row[text]) for row in records}))
    model = KMeans(n_clusters=count, random_state=0, n_init=10).fit(vectors)
    members: dict[int, list[int]] = defaultdict(list)
    for index, label in enumerate(model.labels_):
        members[int(label)].append(index)
    terms = vectorizer.get_feature_names_out()
    distances = model.transform(vectors)
    return [
        {
            "group": label,
            "count": len(indices),
            "terms": ", ".join(terms[model.cluster_centers_[label].argsort()[-5:][::-1]]),
            "representatives": [
                records[i][id_column]
                for i in sorted(indices, key=lambda i: distances[i, label])[:3]
            ],
            "boundary_examples": [
                records[i][id_column]
                for i in sorted(indices, key=lambda i: distances[i, label], reverse=True)[:2]
            ],
        }
        for label, indices in sorted(members.items())
    ]


def conversation_functions(text: str) -> list[str]:
    """Cheap candidate sampling only; flags need review and never assert customer intent."""
    patterns = {
        "correction_candidate": r"\b(actually|correction|i meant|not what|wrong)\b",
        "missing_context_candidate": r"\b(not sure|don't know|missing|unclear)\b",
        "handover_request_candidate": r"\b(human|supervisor|manager|escalate)\b",
    }
    return [name for name, pattern in patterns.items() if re.search(pattern, text, re.I)]
