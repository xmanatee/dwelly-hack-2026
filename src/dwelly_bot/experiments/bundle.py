"""Assigned-case boundary shared by saved grading, reports and exports."""

from typing import Any

from dwelly_bot.storage import fingerprint


def validate(bundle: dict[str, Any]) -> dict[str, Any]:
    """Require an assigned-case denominator and preserve missing results."""
    if (
        type(bundle.get("schema_version")) is not int
        or bundle["schema_version"] != 1
        or not isinstance(bundle.get("runs"), list)
        or not bundle["runs"]
    ):
        raise ValueError("Expected schema_version=1 and at least one run")
    run_ids: set[str] = set()
    for run in bundle["runs"]:
        rid = run["id"]
        if not isinstance(rid, str) or not rid or rid in run_ids:
            raise ValueError("Run IDs must be unique strings")
        run_ids.add(rid)
        assigned = run["manifest"]["assigned_case_ids"]
        if (
            not isinstance(assigned, list)
            or not assigned
            or any(not isinstance(x, str) or not x for x in assigned)
            or len(set(assigned)) != len(assigned)
        ):
            raise ValueError("Provide unique assigned_case_ids, including failed/missing cases")
        if not isinstance(run["cases"], list):
            raise ValueError("Saved cases must be a list")
        assigned_ids = set(assigned)
        cases = {}
        for case in run["cases"]:
            cid = case["id"]
            if not isinstance(cid, str) or not cid or cid in cases or cid not in assigned_ids:
                raise ValueError("Duplicate or unassigned case result")
            cases[cid] = case
        run["cases"] = [
            cases.get(
                cid,
                {
                    "id": cid,
                    "execution_status": "missing_result",
                    "error": "Assigned case has no saved result",
                },
            )
            for cid in assigned
        ]
    return bundle


def verified_outcome(case: dict[str, Any], field: str = "goal_pass") -> bool | None:
    verifier = case.get("verifier", {})
    goal = verifier.get(field)
    return goal if verifier.get("status") == "available" and isinstance(goal, bool) else None


def comparability(
    run: dict[str, Any], case: dict[str, Any], *, evaluation: bool = True
) -> dict[str, Any]:
    """One comparison contract shared by saved grading and the interactive report."""
    manifest = run["manifest"]
    fields = [
        "dataset_hash",
        "environment_version",
        "state_mode",
    ]
    if evaluation:
        fields += ["evaluator_version", "evaluation_profile_hash"]
    reason = None
    if manifest.get("execution_changed_during_run", manifest.get("source_changed_during_run")):
        reason = "Source changed during execution"
    elif manifest.get("state_mode") == "shared":
        reason = "Shared mutable environment; effects are not isolated"
    elif any(not manifest.get(key) for key in fields):
        reason = "Comparison details missing"
    elif not case.get("input_hash"):
        reason = "Case inputs are unconfirmed"
    elif "input" in case and case["input_hash"] != fingerprint(case["input"]):
        reason = "Captured input differs from its fingerprint"
    elif manifest["state_mode"] != "static" and not case.get("initial_state_hash"):
        reason = "Starting state is unconfirmed"
    elif (
        manifest["state_mode"] != "static"
        and "before" in case.get("state_snapshots", {})
        and case["initial_state_hash"] != fingerprint(case["state_snapshots"]["before"])
    ):
        reason = "Captured starting state differs from its fingerprint"
    signature = (
        None
        if reason
        else fingerprint(
            {
                "case_id": case["id"],
                "manifest": {key: manifest.get(key) for key in fields},
                "input": case["input_hash"],
                "initial_state": case.get("initial_state_hash")
                if manifest["state_mode"] != "static"
                else None,
            }
        )
    )
    return {"signature": signature, "reason": reason}
