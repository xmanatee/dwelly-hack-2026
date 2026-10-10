"""Cost/time coverage, skipped/failed attempts and visible saved-report resources."""

import copy
from typing import Any

import pytest

from dwelly_bot.reporting.html import build
from dwelly_bot.reporting.resources import summarize


def attempts() -> list[dict[str, Any]]:
    return [
        {
            "id": "A",
            "execution_status": "completed",
            "metrics": {"latency_ms": 2000, "cost_usd": 0.001, "unconfirmed_exposure_usd": 0},
            "usage": {"requests": 1, "input_tokens": 100, "output_tokens": 10},
        },
        {
            "id": "B",
            "execution_status": "error",
            "metrics": {"latency_ms": 6000, "cost_usd": 0.003, "unconfirmed_exposure_usd": 0},
            "usage": {"requests": 2, "input_tokens": 200, "output_tokens": 20},
        },
        {"id": "C", "execution_status": "not_started"},
    ]


def test_stats_include_failed_work_but_skip_unprocessed_cases_in_price_average() -> None:
    stats = summarize(attempts())
    assert stats["cost_usd"] == pytest.approx(0.004)
    assert stats["cost_mean_usd"] == pytest.approx(0.002)
    assert (
        stats["latency_mean_seconds"],
        stats["latency_min_seconds"],
        stats["latency_max_seconds"],
    ) == (4, 2, 6)
    assert stats["cumulative_case_seconds"] == 8
    assert stats["timed_attempts"] == 2 and stats["requests"] == 3
    assert stats["input_tokens"] == 300 and stats["output_tokens"] == 30


def test_unknown_billing_preserves_known_amount_and_unconfirmed_reservation() -> None:
    rows = attempts()
    rows[1]["metrics"].update(
        cost_usd=None, known_model_cost_usd=0.002, unconfirmed_exposure_usd=0.01
    )
    stats = summarize(rows)
    assert stats["cost_usd"] is stats["cost_mean_usd"] is None
    assert stats["known_cost_usd"] == pytest.approx(0.003)
    assert stats["unconfirmed_exposure_usd"] == 0.01
    missing = summarize(rows, assigned=4)
    assert missing["unconfirmed_exposure_usd"] is missing["requests"] is None


def test_offline_control_zero_cost_does_not_display_theoretical_provider_charges() -> None:
    rows = attempts()[:1]
    rows[0]["metrics"].update(
        cost_usd=0, known_model_cost_usd=99, cost_kind="offline_control_not_billed"
    )
    assert summarize(rows)["known_cost_usd"] == summarize(rows)["cost_usd"] == 0


@pytest.mark.parametrize("value", [-1, float("nan"), float("inf"), True, "1.5"])
def test_invalid_resource_measurement_is_an_error(value: Any) -> None:
    rows = attempts()
    rows[0]["metrics"]["latency_ms"] = value
    with pytest.raises(ValueError, match="finite nonnegative"):
        summarize(rows)


def test_resource_report_exposes_model_stats_without_rewriting_saved_results() -> None:
    bundle: dict[str, Any] = {
        "schema_version": 1,
        "runs": [
            {
                "id": "run",
                "manifest": {
                    "assigned_case_ids": ["A", "B", "C"],
                    "model": "provider/model",
                    "resolved_config": {"provider": "openrouter", "case_concurrency": 2},
                },
                "cases": attempts(),
            }
        ],
    }
    original = copy.deepcopy(bundle)
    report = build(bundle)
    assert bundle == original
    totals = {
        row["Metric"]: row["Value"]
        for b in report.blocks
        if b.title == "Resource totals"
        for row in b.data["rows"]
    }
    assert totals["Execution cost (USD)"] == pytest.approx(0.004)
    assert totals["Mean case time (s)"] == 4
    rows = next(b.data["rows"] for b in report.blocks if b.title == "Run resources")
    assert rows[0]["Model"] == "provider/model" and rows[0]["Timed"] == 2
    assert rows[0]["Mean processing cost (USD)"] == pytest.approx(0.002)
    bundle["runs"][0]["cases"] = attempts()[:1]
    incomplete = build(bundle)
    totals = {
        row["Metric"]: row["Value"]
        for b in incomplete.blocks
        if b.title == "Resource totals"
        for row in b.data["rows"]
    }
    assert totals["Execution cost (USD)"] is None
    assert totals["Known cost (USD)"] == 0.001


@pytest.mark.parametrize(
    "section,field,value",
    [
        ("metrics", "latency_ms", 0),
        ("metrics", "cost_usd", 1),
        ("metrics", "known_model_cost_usd", 1),
        ("metrics", "unconfirmed_exposure_usd", 1),
        ("usage", "requests", 1),
        ("usage", "input_tokens", 1),
        ("usage", "output_tokens", 1),
    ],
)
def test_skipped_status_cannot_hide_processing(section: str, field: str, value: int) -> None:
    rows = attempts()
    rows[2][section] = {field: value}
    with pytest.raises(ValueError, match="not-started"):
        summarize(rows)
