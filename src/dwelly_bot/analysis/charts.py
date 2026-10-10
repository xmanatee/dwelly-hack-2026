"""Task-shaped charts. Callers supply labels, units, meanings and optional drilldown IDs."""

import math
from bisect import bisect_right
from collections import defaultdict
from collections.abc import Mapping, Sequence
from typing import Any

from dwelly_bot.analysis.data import Table
from dwelly_bot.contracts import JsonRecord
from dwelly_bot.reporting.theme import DISPLAY, PALETTE, TOKENS


def ranking(
    rows: list[JsonRecord],
    label: str,
    value: str = "count",
    *,
    unit: str,
    id_column: str | None = None,
) -> Any:
    from plotly import graph_objects as go

    ordered = sorted(rows, key=lambda row: float(row[value]), reverse=True)
    fig = go.Figure(
        go.Bar(
            y=[str(row[label]) for row in ordered],
            x=[row[value] for row in ordered],
            orientation="h",
            marker_color=TOKENS["accent"],
            text=[row[value] for row in ordered],
            texttemplate="%{text:,}",
            textposition="outside",
            cliponaxis=False,
            customdata=[row[id_column or label] for row in ordered],
            hovertemplate="%{y}<br>%{x:,} " + unit + "<extra></extra>",
        )
    )
    fig.update_layout(
        height=max(270, len(ordered) * 27 + 85),
        showlegend=False,
        xaxis={"title": unit, "rangemode": "tozero"},
        yaxis={"autorange": "reversed", "showgrid": False, "type": "category"},
    )
    return fig


def composition(
    rows: list[JsonRecord],
    group: str,
    category: str,
    value: str = "count",
    *,
    colors: Mapping[str, str] | None = None,
) -> Any:
    """100% stacked bars, with explicit raw count and per-group denominator in hover."""
    from plotly import graph_objects as go

    totals: dict[str, float] = defaultdict(float)
    values: dict[tuple[str, str], float] = defaultdict(float)
    categories: list[str] = []
    for row in rows:
        amount = float(row[value])
        if amount < 0:
            raise ValueError("Composition counts must be nonnegative")
        g, c = str(row[group]), str(row[category])
        totals[g] += amount
        values[g, c] += amount
        if c not in categories:
            categories.append(c)
    groups = list(totals)
    fig = go.Figure()
    for index, c in enumerate(categories):
        shares = [100 * values[g, c] / totals[g] if totals[g] else 0 for g in groups]
        fig.add_bar(
            name=c,
            y=[f"{g} · n={totals[g]:,.0f}" for g in groups],
            x=shares,
            orientation="h",
            marker_color=(colors or {}).get(c, PALETTE[index % len(PALETTE)]),
            customdata=[[values[g, c], totals[g]] for g in groups],
            text=[
                f"{share:.{DISPLAY['percent_decimals']}f}%" if share >= 7 else ""
                for share in shares
            ],
            textposition="inside",
            hovertemplate=c
            + f"<br>%{{x:.{DISPLAY['percent_decimals']}f}}% · %{{customdata[0]:,}} / %{{customdata[1]:,}}<extra></extra>",
        )
    fig.update_layout(
        barmode="stack",
        height=max(260, len(groups) * 38 + 140),
        xaxis={"title": "Share of each group", "range": [0, 100], "ticksuffix": "%"},
        yaxis={"autorange": "reversed", "showgrid": False, "type": "category"},
    )
    return fig


def matrix(
    rows: list[JsonRecord],
    row: str,
    column: str,
    value: str,
    *,
    unit: str,
    fill: float | None = None,
) -> Any:
    from plotly import graph_objects as go

    ys = list(dict.fromkeys(str(item[row]) for item in rows))
    xs = list(dict.fromkeys(str(item[column]) for item in rows))
    cells: dict[tuple[str, str], float] = defaultdict(float)
    for item in rows:
        cells[str(item[row]), str(item[column])] += float(item[value])
    z = [[cells.get((y, x), fill) for x in xs] for y in ys]
    fig = go.Figure(
        go.Heatmap(
            x=xs,
            y=ys,
            z=z,
            text=z,
            texttemplate="%{text:,}",
            hoverongaps=False,
            colorscale=[[0, "#eef3eb"], [1, TOKENS["accent"]]],
            colorbar={"title": unit, "thickness": 10},
            hovertemplate="%{y} · %{x}<br>%{z:,} " + unit + "<extra></extra>",
        )
    )
    fig.update_layout(
        height=max(290, len(ys) * 35 + 90),
        yaxis={"autorange": "reversed", "showgrid": False, "type": "category"},
        xaxis={"showgrid": False, "type": "category"},
    )
    return fig


def availability(
    rows: list[JsonRecord],
    id_column: str,
    fields: Sequence[tuple[str, str]],
) -> Any:
    """Presence only; never interpret supplied evidence as successful extraction or resolution."""
    from plotly import graph_objects as go

    statuses = {True: (2, "Available"), False: (0, "Absent"), None: (1, "Unknown")}
    z, text, ids = [], [], []
    for row in rows:
        values = [statuses[row.get(field)] for field, _ in fields]
        z.append([v[0] for v in values])
        text.append([v[1] for v in values])
        ids.append([str(row[id_column])] * len(fields))
    fig = go.Figure(
        go.Heatmap(
            x=[label for _, label in fields],
            y=[str(row[id_column]) for row in rows],
            z=z,
            text=text,
            texttemplate="%{text}",
            customdata=ids,
            zmin=0,
            zmax=2,
            colorscale=[
                [0, "#e4b1a1"],
                [0.249, "#e4b1a1"],
                [0.25, "#e3d5ad"],
                [0.749, "#e3d5ad"],
                [0.75, "#b7d5bd"],
                [1, "#b7d5bd"],
            ],
            showscale=False,
            xgap=3,
            ygap=3,
            hovertemplate="%{y} · %{x}<br>%{text}<extra></extra>",
        )
    )
    fig.update_layout(
        height=max(270, len(rows) * 30 + 85),
        yaxis={"autorange": "reversed", "showgrid": False, "type": "category"},
        xaxis={"side": "top", "showgrid": False, "type": "category"},
    )
    return fig


def cumulative(table: Table, column: str, *, unit: str, log_x: bool = False) -> Any:
    from plotly import graph_objects as go

    table.require(column)
    values = sorted(float(row[column]) for row in table.rows if row.get(column) is not None)
    if any(not math.isfinite(v) for v in values):
        raise ValueError("Cumulative distribution requires finite values")
    if log_x and values and values[0] <= 0:
        raise ValueError("Log scale requires positive values; choose a linear scale")
    if not values:
        return go.Figure()
    points = sorted({values[int((len(values) - 1) * i / 200)] for i in range(201)})
    fig = go.Figure(
        go.Scatter(
            x=points,
            y=[100 * bisect_right(values, p) / len(values) for p in points],
            mode="lines+markers" if len(points) == 1 else "lines",
            line={"width": 2, "color": TOKENS["accent"]},
            hovertemplate=f"≤ %{{x:,.{DISPLAY['decimals']}f}} "
            + unit
            + f"<br>%{{y:.{DISPLAY['percent_decimals']}f}}% of records<extra></extra>",
        )
    )
    fig.update_layout(
        showlegend=False,
        xaxis={
            "title": unit + (" · log scale" if log_x else ""),
            "type": "log" if log_x else "linear",
        },
        yaxis={"title": "Records at or below this value", "range": [0, 100], "ticksuffix": "%"},
    )
    return fig
