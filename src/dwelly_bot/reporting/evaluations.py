"""Discover saved assessment fields without a report-specific metric registry."""

from collections import Counter
from typing import Any

from dwelly_bot.experiments.bundle import comparability
from dwelly_bot.storage import fingerprint


def judge_summary(bundle: dict[str, Any]) -> list[dict[str, Any]]:
    """Keep model judgments separate from independently verified operational outcomes."""
    rows = []
    for run in bundle["runs"]:
        criteria = {
            item["criterion"]: item.get("label", item["criterion"])
            for case in run["cases"]
            for item in case.get("judge", [])
        }
        for criterion, label in criteria.items():
            counts = Counter(
                item["status"]
                for case in run["cases"]
                if case.get("judge_status") == "available"
                for item in case.get("judge", [])
                if item["criterion"] == criterion
            )
            rows.append(
                {
                    "Run": run.get("label", run["id"]),
                    "Criterion": label,
                    "Pass": counts["pass"],
                    "Fail": counts["fail"],
                    "Unknown": counts["unknown"],
                    "Not reviewed": len(run["cases"]) - sum(counts.values()),
                    "Assigned": len(run["cases"]),
                }
            )
    return rows


def measurements(case: dict[str, Any], manifest: dict[str, Any]) -> dict[str, dict[str, Any]]:
    result = {}
    verifier = case.get("verifier", {})
    groups = {
        "check": verifier.get("checks", []),
        "flag": verifier.get("red_flags", []),
        "judge": case.get("judge", []),
    }
    for kind, items in groups.items():
        for item in items:
            key = str(item.get("id") or item.get("criterion"))
            result[f"{kind}/{key}"] = {
                **item,
                "value": item.get(
                    "value", item.get("status", "flagged" if kind == "flag" else None)
                ),
            }
    for kind, items in {
        "metric": verifier.get("metrics", {}),
        "assessment": case.get("assessments", {}),
    }.items():
        for key, value in items.items():
            result[f"{kind}/{key}"] = dict(value) if isinstance(value, dict) else {"value": value}
    for key, item in result.items():
        item.setdefault("label", key)
        item["version"] = item.get("version") or manifest.get("evaluation_profile_hash")
        if (key.startswith(("check/", "metric/")) and verifier.get("status") != "available") or (
            key.startswith("judge/") and case.get("judge_status") != "available"
        ):
            item["value"] = None
    return result


def evaluation_rows(bundle: dict[str, Any]) -> list[dict[str, Any]]:
    runs = bundle["runs"]
    if bundle.get("comparisons"):
        pair = bundle["comparisons"][0]
        runs = [
            next(r for r in runs if r["id"] == pair[role]) for role in ("baseline", "candidate")
        ]
    indexed = [{case["id"]: case for case in run["cases"]} for run in runs]
    rows = []
    for cid in indexed[0]:
        cases = [lookup[cid] for lookup in indexed]
        values = [
            measurements(case, run["manifest"]) for case, run in zip(cases, runs, strict=True)
        ]
        signatures = [
            comparability(run, case, evaluation=False)["signature"]
            for case, run in zip(cases, runs, strict=True)
        ]
        for key in sorted(set().union(*(value.keys() for value in values))):
            items = [value.get(key) for value in values]
            present = [item for item in items if item is not None]
            numeric: list[Any] = [item.get("value") if item else None for item in items]
            comparable = (
                len(items) == 2
                and all(item is not None for item in items)
                and signatures[0] is not None
                and len(set(signatures)) == 1
                and present[0].get("version") is not None
                and len({fingerprint([item.get("version"), item.get("unit")]) for item in present})
                == 1
            )
            status = (
                "comparable"
                if comparable
                else "not measured on both runs"
                if len(present) != len(items)
                else "different or unconfirmed definitions"
                if len(items) == 2
                else "recorded"
            )
            fields = {
                "Case": cid,
                "Metric": key,
                "Comparison": status,
                **{
                    ("Baseline" if i == 0 else "Experiment")
                    if len(items) == 2
                    else "Value": item.get("value") if item else "not measured"
                    for i, item in enumerate(items)
                },
                "Delta": numeric[1] - numeric[0]
                if comparable and all(type(v) in {int, float} for v in numeric)
                else None,
                "Unit": present[0].get("unit"),
                "Reason": " | ".join(str(item["reason"]) for item in present if item.get("reason")),
            }
            rows.append(
                {
                    "id": fingerprint([cid, key]),
                    "title": f"{present[0].get('label') or key} · {cid}",
                    "fields": fields,
                }
            )
    return rows
