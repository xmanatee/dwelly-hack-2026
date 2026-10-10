"""Visual contracts: honest denominators, missing cells and stable point identities."""

import json
import warnings
from pathlib import Path
from typing import Any

import pytest

pytest.importorskip("plotly")

from dwelly_bot.analysis import Report, Table
from dwelly_bot.analysis.charts import availability, composition, cumulative, matrix, ranking
from dwelly_bot.analysis.discovery_types import DiscoveryRecord
from dwelly_bot.analysis.recipes import histogram, numeric_summary, text_groups
from dwelly_bot.analysis.semantic import semantic_groups
from dwelly_bot.reporting import render
from dwelly_bot.reporting.theme import TOKENS


def test_histogram_preserves_valid_counts_and_reports_excluded_observations() -> None:
    data = Table("numbers", [{"value": v} for v in [1, 2, None, "bad", float("nan")]])
    summary = numeric_summary(data, "value")
    chart = histogram(data, "value", bins=3)
    assert sum(chart.data[0].y) == summary["valid"] == 2
    assert "3 missing or invalid" in chart.layout.title.text
    with pytest.raises(ValueError, match="finite numeric"):
        histogram(Table("empty", [{"value": "bad"}]), "value")


@pytest.mark.parametrize("texts", [["one"], ["the", "and", "or"]])
def test_unusable_text_cannot_be_presented_as_successful_groups(texts: list[str]) -> None:
    rows = [{"id": str(i), "text": text} for i, text in enumerate(texts)]
    with pytest.raises(ValueError):
        text_groups(Table("texts", rows), "text", "id")


def test_shares_keep_each_group_denominator_and_counts() -> None:
    fig = composition(
        [
            {"g": "one", "c": "yes", "count": 1},
            {"g": "one", "c": "no", "count": 3},
            {"g": "two", "c": "yes", "count": 8},
            {"g": "two", "c": "no", "count": 2},
        ],
        "g",
        "c",
    )
    assert list(fig.data[0].x) == [25, 80]
    assert list(fig.data[1].x) == [75, 20]
    assert list(fig.data[0].customdata[0]) == [1, 4]
    assert fig.layout.xaxis.range == (0, 100)


def test_ranking_and_missing_matrix_are_not_silent_zeroes() -> None:
    fig = ranking([{"id": "a", "n": 2}, {"id": "b", "n": 7}], "id", "n", unit="Cases")
    assert list(fig.data[0].y) == ["b", "a"]
    assert list(fig.data[0].customdata) == ["b", "a"]
    assert fig.layout.xaxis.rangemode == "tozero"
    grid = matrix(
        [{"r": "one", "c": "x", "n": 2}, {"r": "two", "c": "y", "n": 3}],
        "r",
        "c",
        "n",
        unit="Cases",
    )
    assert grid.data[0].z[0][1] is None
    zero = matrix(
        [{"r": "one", "c": "x", "n": 2}, {"r": "two", "c": "y", "n": 3}],
        "r",
        "c",
        "n",
        unit="Cases",
        fill=0,
    )
    assert zero.data[0].z[0][1] == 0


def test_availability_keeps_unknown_and_click_targets() -> None:
    fig = availability(
        [{"id": "case", "yes": True, "no": False, "unknown": None}],
        "id",
        [("yes", "Present"), ("no", "Absent"), ("unknown", "Unknown")],
    )
    assert list(fig.data[0].z[0]) == [2, 0, 1]
    assert list(fig.data[0].customdata[0]) == ["case"] * 3
    assert list(fig.data[0].text[0]) == ["Available", "Absent", "Unknown"]


def test_cumulative_curve_includes_tail_and_rejects_false_log_scale() -> None:
    fig = cumulative(
        Table("amounts", [{"v": 1}, {"v": 1}, {"v": 10000}]), "v", unit="EUR", log_x=True
    )
    assert list(fig.data[0].x) == [1, 10000]
    assert fig.data[0].y[-1] == 100
    assert fig.data[0].y[0] == pytest.approx(200 / 3)
    with pytest.raises(ValueError, match="positive"):
        cumulative(Table("amounts", [{"v": 0}, {"v": 1}]), "v", unit="EUR", log_x=True)


def test_theme_preserves_explicit_labels_and_does_not_mutate_input(tmp_path: Path) -> None:
    fig = ranking([{"id": "x", "count": 2}], "id", unit="Customers")
    original: Any = fig.to_plotly_json()
    report = Report(title="probe")
    report.chart(
        "A question",
        fig,
        caption="Known scope",
        note="Recipe-owned method",
        details={"x": {"title": "Customer", "fields": {"Count": 2}}},
    )
    output = tmp_path / "report.html"
    render(report, output)
    payload = (
        output.read_text()
        .split('<script id="report-data" type="application/json">')[1]
        .split("</script>")[0]
    )
    layout = json.loads(payload)["blocks"][0]["data"]["layout"]
    assert layout["xaxis"]["title"]["text"] == "Customers"
    assert layout["template"]["layout"]["font"]["color"] == TOKENS["ink"]
    assert report.blocks[0].data["details"]["x"]["fields"]["Count"] == 2
    assert fig.to_plotly_json() == original


def test_identical_vectors_keep_all_records_without_invalid_projection() -> None:
    records = [
        DiscoveryRecord(id=str(i), title="Same record", sources=[], kind="policy") for i in range(3)
    ]
    with warnings.catch_warnings():
        warnings.simplefilter("error", RuntimeWarning)
        result = semantic_groups(records, [[1.0, 0.0]] * len(records))
    assert {row["id"] for row in result["assignments"]} == {record.id for record in records}
    assert all(row["projection_x"] == row["projection_y"] == 0 for row in result["assignments"])
