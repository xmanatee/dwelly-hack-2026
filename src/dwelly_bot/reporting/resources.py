"""Resource statistics from captured attempts; unknown billing stays unknown."""

import math
from collections.abc import Sequence
from statistics import mean
from typing import Any


def _number(value: Any) -> int | float | None:
    if value is None:
        return None
    if (
        isinstance(value, bool)
        or not isinstance(value, int | float)
        or not math.isfinite(value)
        or value < 0
    ):
        raise ValueError("Resource measurements must be finite nonnegative numbers")
    return value


def summarize(cases: Sequence[dict[str, Any]], assigned: int | None = None) -> dict[str, Any]:
    expected = len(cases) if assigned is None else assigned
    if type(expected) is not int or expected < len(cases):
        raise ValueError("Captured resource rows exceed assigned attempts")
    previous = [attempt for case in cases for attempt in case.get("previous_attempts", [])]
    cases = [*cases, *previous]
    expected += len(previous)
    times: list[float] = []
    costs: list[int | float] = []
    known: list[int | float] = []
    exposure: list[int | float] = []
    usage: dict[str, list[int | float]] = {
        key: [] for key in ("requests", "input_tokens", "output_tokens")
    }
    processed = 0
    for case in cases:
        metrics = {
            key: _number(case.get("metrics", {}).get(key))
            for key in (
                "latency_ms",
                "cost_usd",
                "known_model_cost_usd",
                "unconfirmed_exposure_usd",
            )
        }
        counters = {key: _number(case.get("usage", {}).get(key)) for key in usage}
        if any(value is not None and value != int(value) for value in counters.values()):
            raise ValueError("SDK usage counters must be whole numbers")
        skipped = case.get("execution_status") == "not_started"
        if skipped and (
            metrics["latency_ms"] is not None
            or any(value not in {None, 0} for value in [*metrics.values(), *counters.values()])
        ):
            raise ValueError("A not-started case cannot contain processing measurements")
        processed += not skipped
        latency = metrics["latency_ms"]
        if latency is not None:
            times.append(latency / 1000)
        cost = 0 if skipped else metrics["cost_usd"]
        partial = cost if cost is not None else metrics["known_model_cost_usd"]
        uncertain = 0 if skipped else metrics["unconfirmed_exposure_usd"]
        for values, value in [(costs, cost), (known, partial), (exposure, uncertain)]:
            if value is not None:
                values.append(value)
        for key, values in usage.items():
            value = 0 if skipped else counters[key]
            if value is not None:
                values.append(value)
    complete = len(costs) == expected
    return {
        "timed_attempts": len(times),
        "costed_attempts": len(costs),
        "latency_mean_seconds": mean(times) if times else None,
        "latency_min_seconds": min(times) if times else None,
        "latency_max_seconds": max(times) if times else None,
        "cumulative_case_seconds": sum(times) if times else None,
        "cost_usd": sum(costs) if complete else None,
        "cost_mean_usd": sum(costs) / processed if complete and processed else None,
        "known_cost_usd": sum(known) if known else None,
        "unconfirmed_exposure_usd": sum(exposure) if len(exposure) == expected else None,
        **{
            key: int(sum(values)) if len(values) == expected else None
            for key, values in usage.items()
        },
    }
