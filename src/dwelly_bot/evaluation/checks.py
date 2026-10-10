"""Deterministic checks over saved observations, separate from model reviews."""

import json
import re
from typing import Any


def pointer(value: Any, path: str) -> tuple[bool, Any]:
    """JSON Pointer; a missing observation is unknown, never an invented value."""
    if (path and not path.startswith("/")) or re.search(r"~(?![01])", path):
        raise ValueError("Invalid RFC 6901 JSON Pointer")
    if not path:
        return True, value
    try:
        for key in path[1:].split("/"):
            key = key.replace("~1", "/").replace("~0", "~")
            if isinstance(value, list):
                if key == "-":
                    return False, None
                if not re.fullmatch(r"0|[1-9][0-9]*", key):
                    raise ValueError(
                        "JSON Pointer array indices must be unsigned without leading zeros"
                    )
                value = value[int(key)]
            else:
                value = value[key]
        return True, value
    except (KeyError, IndexError, TypeError):
        return False, None


def hard_checks(case: dict[str, Any], contract: dict[str, Any]) -> dict[str, Any]:
    json.dumps((case, contract), allow_nan=False)
    checks = []
    identifiers: set[str] = set()
    for rule in contract.get("checks", []):
        if rule["id"] in identifiers or rule["id"] == "answer-captured":
            raise ValueError("Check IDs must be unique")
        identifiers.add(rule["id"])
        operators = set(rule) & {"equals", "one_of", "contains", "minimum", "maximum", "exists"}
        if len(operators) != 1:
            raise ValueError("Each check requires exactly one explicit predicate")
        if rule.get("kind") == "goal" and not rule["path"].startswith("/state_snapshots/"):
            raise ValueError(
                "Goal predicates must inspect independent state snapshots, not agent claims"
            )
        found, value = pointer(case, rule["path"])
        if "exists" in rule:
            if not isinstance(rule["exists"], bool):
                raise ValueError("exists must be a boolean")
            parent_path = rule["path"].rsplit("/", 1)[0]
            parent_known = pointer(case, parent_path)[0] if parent_path else True
            verdict = (
                "unknown" if not parent_known else "pass" if found is rule["exists"] else "fail"
            )
            reason = f"Observation exists: {found}."
        elif not found:
            verdict, reason = "unknown", "Required observation was not captured."
        elif "equals" in rule:
            verdict = (
                "pass"
                if type(value) is type(rule["equals"]) and value == rule["equals"]
                else "fail"
            )
            reason = f"Observed {value!r}; required {rule['equals']!r}."
        elif "one_of" in rule:
            verdict = (
                "pass"
                if any(type(value) is type(item) and value == item for item in rule["one_of"])
                else "fail"
            )
            reason = "Observed value compared with reviewed acceptable alternatives."
        elif "contains" in rule:
            if not isinstance(value, (str, list, dict)):
                raise ValueError("contains requires a string, list or mapping observation")
            verdict = "pass" if rule["contains"] in value else "fail"
            reason = "Observed collection compared with reviewed required member."
        else:
            name = next(iter(operators))
            threshold = rule[name]
            if type(value) not in {int, float} or type(threshold) not in {int, float}:
                raise ValueError("Numeric predicates require numeric observations and thresholds")
            passed = value >= threshold if name == "minimum" else value <= threshold
            verdict = "pass" if passed else "fail"
            reason = f"Observed {value!r}; {name} {threshold!r}."
        checks.append(
            {
                "id": rule["id"],
                "label": rule.get("label", rule["id"]),
                "status": verdict,
                "reason": reason,
                "dimension": rule.get("kind", "requirement"),
                "evidence_path": rule["path"],
            }
        )
    # These are inspection checks, not a business-goal accuracy score.
    checks.append(
        {
            "id": "answer-captured",
            "label": "Final answer was captured",
            "status": "pass" if case.get("answer") is not None else "fail",
            "reason": "Saved output exists."
            if case.get("answer") is not None
            else "No saved final output.",
            "dimension": "artifact",
        }
    )
    goals = [c["status"] for c in checks if c["dimension"] == "goal"]
    safety = [c["status"] for c in checks if c["dimension"] == "safety"]
    goal = (
        False
        if "fail" in goals
        else True
        if goals
        and contract.get("goal_contract_complete") is True
        and all(x == "pass" for x in goals)
        else None
    )
    critical = (
        True
        if "fail" in safety
        else False
        if safety
        and contract.get("safety_contract_complete") is True
        and all(x == "pass" for x in safety)
        else None
    )
    return {
        "status": "available",
        "goal_pass": goal,
        "critical_failure": critical,
        "checks": checks,
        "score": None,
        "score_kind": "No numeric business score defined",
        "red_flags": inspection_flags(case),
    }


def inspection_flags(case: dict[str, Any]) -> list[dict[str, Any]]:
    """Observable review signals; these are not accuracy labels or policy verdicts."""
    flags = []
    if case.get("execution_status") != "completed":
        flags.append({"id": "execution_incomplete", "evidence": "execution_status"})
    for event in case.get("tool_events", []):
        write = event.get("read_only") is False
        if write and event.get("status") in {"started", "unconfirmed", "error"}:
            flags.append(
                {
                    "id": "write_requires_reconciliation",
                    "evidence": event.get("id"),
                    "status": event.get("status"),
                }
            )
    if case.get("agent_disposition") == "completed" and case.get("answer") is None:
        flags.append({"id": "completion_without_answer", "evidence": "answer"})
    return flags
