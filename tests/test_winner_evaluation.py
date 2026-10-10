"""Decision cut isolation and saved-result provenance; no paid calls."""

from pathlib import Path
from typing import Any

import pytest

from dwelly_bot.adapters.banking_scenarios import prepare
from dwelly_bot.contracts import RunConfig
from dwelly_bot.evaluation.winner import evidence, summarize
from dwelly_bot.storage import load_json, save_json
from hackathon_winner.adapters import load


def fixture(tmp_path: Path) -> tuple[Path, Path, Path]:
    track = tmp_path / "source"
    case = track / "001"
    (case / "attachments").mkdir(parents=True)
    (case / "index.md").write_text("SECRET_OUTCOME_TITLE")
    (case / "attachments/early.txt").write_text("EARLY_FILE")
    (case / "attachments/late.txt").write_text("FUTURE_FILE")
    history = "# SECRET_OUTCOME_TITLE\nTotal events: 3\n\n"
    for i, body in enumerate(("Please check my transfer", "EXPECTED_ACTION", "FUTURE_RESULT"), 1):
        history += (
            f"## 2025-01-01 0{i}:00:00 UTC — event {i:03d}\n\n"
            "- **Channel:** Secure chat\n- **From:** Customer\n- **To:** Bank\n\n" + body + "\n\n"
        )
    (case / "history.md").write_text(history)
    spec, availability = tmp_path / "spec.json", tmp_path / "availability.json"
    save_json(spec, {"decision_events": {"001": [2]}})
    save_json(
        availability,
        {
            "attachments": {
                "001": [
                    {"path": "attachments/early.txt", "available_after_event": 1},
                    {"path": "attachments/late.txt", "available_after_event": 3},
                ]
            }
        },
    )
    prepared = tmp_path / "prepared"
    prepare(track, prepared, spec, availability)
    return prepared, spec, track


def test_cut_keeps_reference_and_future_out_of_winner(tmp_path: Path) -> None:
    prepared, _, _ = fixture(tmp_path)
    cases = load(prepared / "inputs", RunConfig(), prefix="")
    assert len(cases) == 1
    source = cases[0].source.model_dump_json()
    assert "EARLY_FILE" in source
    for hidden in (
        "SECRET_OUTCOME_TITLE",
        "EXPECTED_ACTION",
        "FUTURE_RESULT",
        "FUTURE_FILE",
        "Total events",
    ):
        assert hidden not in source
    assert not cases[0].source.events  # One complete text document, not a misparsed final event.
    assert len(cases[0].source.documents) == 1
    assert "EXPECTED_ACTION" in (prepared / "references/001-e002/action.md").read_text()


def test_requires_explicit_population_and_attachment_review(tmp_path: Path) -> None:
    _, spec, track = fixture(tmp_path)
    save_json(spec, {"decision_events": {}}, overwrite=True)
    with pytest.raises(ValueError, match="every source scenario"):
        prepare(track, tmp_path / "other", spec, tmp_path / "availability.json")
    save_json(spec, {"decision_events": {"001": [2]}}, overwrite=True)
    (track / "001/attachments/unreviewed.txt").write_text("unknown availability")
    with pytest.raises(ValueError, match="Unreviewed attachment"):
        prepare(track, tmp_path / "other", spec, tmp_path / "availability.json")


def prediction(prepared: Path, output: Path) -> None:
    case = load(prepared / "inputs", RunConfig(), prefix="")[0]
    folder = output / case.case_id
    folder.mkdir(parents=True)
    plan: dict[str, Any] = {"steps": []}
    for name, body in (
        ("context.md", case.history),
        ("ANSWER.md", "Proposal"),
        ("REASONING.md", "Evidence"),
    ):
        (folder / name).write_text(body)
    save_json(folder / "plan.json", plan)
    save_json(
        folder / "generation.json",
        {
            "context": case.history,
            "plan": plan,
            "output": {"answer": "Proposal", "reasoning": "Evidence"},
        },
    )
    save_json(
        output / "predictions.json",
        {
            "cases": [
                {
                    "case_id": case.case_id,
                    "input_files": case.input_files,
                    "error": None,
                    "cost_usd": 0,
                }
            ]
        },
    )


def test_saved_output_must_match_context_and_generation(tmp_path: Path) -> None:
    prepared, _, _ = fixture(tmp_path)
    output = tmp_path / "winner"
    prediction(prepared, output)
    cases, refs = evidence(prepared, output)
    assert len(cases) == len(refs) == 1
    (output / "001-e002/ANSWER.md").write_text("altered")
    with pytest.raises(ValueError, match="Conflicting saved"):
        evidence(prepared, output)


def test_changed_reference_and_missing_case_rejected(tmp_path: Path) -> None:
    prepared, _, _ = fixture(tmp_path)
    output = tmp_path / "winner"
    prediction(prepared, output)
    path = prepared / "references/001-e002/action.md"
    path.write_text(path.read_text() + "silently changed")
    with pytest.raises(ValueError, match="Prepared evidence changed"):
        evidence(prepared, output)
    save_json(output / "predictions.json", {"cases": []}, overwrite=True)
    with pytest.raises(ValueError, match="exactly all"):
        evidence(prepared, output)


def test_unknowns_and_failures_stay_in_denominator() -> None:
    rubric = load_json(Path("src/dwelly_bot/evaluation/rubrics/winner-reference.json"))
    findings = [{"criterion": c["id"], "status": "pass"} for c in rubric["criteria"]]
    rows = [
        {
            "scenario": "001",
            "execution_status": "success",
            "judge_status": "available",
            "judge": findings,
            "winner_metrics": {"cost_usd": 0},
        }
    ]
    rows.append(
        {
            "scenario": "002",
            "execution_status": "error",
            "judge_status": "not_run",
            "judge": [],
            "winner_metrics": {"cost_usd": 0},
        }
    )
    summary = summarize(rows)
    assert summary["assigned"] == 2 and summary["all_core_pass"] == 1
    assert summary["criteria"]["plan_action"] == {"pass": 1, "not_assessed": 1}
    findings[0]["status"] = "unknown"
    assert summarize(rows)["all_core_pass"] == 0
