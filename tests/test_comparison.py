"""Frozen experiments, fair case pairing and deliberate baseline adoption."""

import copy
import json
from pathlib import Path
from typing import Any

import pytest

from dwelly_bot.cli import main
from dwelly_bot.contracts import RunConfig
from dwelly_bot.experiments.comparison import Comparison, SavedRun
from dwelly_bot.experiments.provenance import execution_hash, source_hash
from dwelly_bot.reporting.html import build, comparison_rows, render
from dwelly_bot.storage import fingerprint, save_json


def saved(path: Path, name: str, outcomes: list[bool | None]) -> dict[str, Any]:
    bundle = {
        "schema_version": 1,
        "runs": [
            {
                "id": name,
                "manifest": {
                    "assigned_case_ids": [str(i) for i in range(len(outcomes))],
                    "dataset": "authored-report-fixture",
                    "dataset_hash": "same-corpus",
                    "environment_version": "fixture-v1",
                    "evaluator_version": "fixture-v1",
                    "evaluation_profile_hash": "same-checked-contract",
                    "state_mode": "isolated",
                    "resolved_config": RunConfig().model_dump(mode="json"),
                    "code_revision": source_hash(),
                    "execution_hash": execution_hash(),
                },
                "cases": [
                    {
                        "id": str(i),
                        "title": f"Fixture case {i}",
                        "input": {"question": f"Resolve synthetic request {i}"},
                        "input_hash": fingerprint({"question": f"Resolve synthetic request {i}"}),
                        "initial_state_hash": fingerprint({}),
                        "execution_status": "completed",
                        "answer": f"{name} answer {i}",
                        "tool_events": [
                            {"tool": "fixture", "status": "returned", "result": outcome}
                        ],
                        "state_snapshots": {"before": {}, "after": {"done": outcome}},
                        "verifier": {"status": "available", "goal_pass": outcome},
                    }
                    for i, outcome in enumerate(outcomes)
                ],
            }
        ],
        "notice": "Authored report fixture; not model-quality evidence",
    }
    save_json(path, bundle)
    return bundle


@pytest.fixture
def experiment(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Comparison:
    from types import SimpleNamespace

    from dwelly_bot.experiments import comparison

    monkeypatch.setattr(comparison, "ROOT", tmp_path / "workspace")
    monkeypatch.setattr(
        comparison,
        "adapter_for",
        lambda _: SimpleNamespace(dataset_root=tmp_path, state_mode="isolated"),
    )
    monkeypatch.setattr(comparison, "dataset_hash", lambda _: "same-corpus")
    monkeypatch.setattr(comparison, "evaluator_hash", lambda *_: "same-checked-contract")
    config = tmp_path / "config.json"
    save_json(config, RunConfig().model_dump(mode="json"))
    baseline, candidate = tmp_path / "baseline-result.json", tmp_path / "candidate-result.json"
    saved(baseline, "before", [False, True, None, True])
    saved(candidate, "after", [True, False, True, True])
    return Comparison(
        title="Report contract fixture",
        description="Exercise improvement, regression, unknown and unchanged outcomes",
        baseline=SavedRun.freeze(baseline, config_path=config),
        candidate=SavedRun.freeze(candidate, config_path=config),
    )


def test_report_embeds_both_traces_and_only_declared_comparisons(
    tmp_path: Path, experiment: Comparison
) -> None:
    bundle = experiment.bundle()
    assert [row["change"] for row in comparison_rows(bundle)] == [
        "improved",
        "regressed",
        "unknown",
        "unchanged",
    ]
    output = tmp_path / "report.html"
    render(bundle, output)
    payload = json.loads(
        output.read_text()
        .split('<script id="report-data" type="application/json">')[1]
        .split("</script>")[0]
    )
    cases = [
        row
        for block in payload["blocks"]
        if block["kind"] == "records"
        for row in block["data"]["rows"]
        if "raw_capture" in row
    ]
    assert [row["raw_capture"] for row in cases] == [
        case for run in bundle["runs"] for case in run["cases"]
    ]
    assert payload["receipt"]["experiment"] == experiment.model_dump()
    assert [run["manifest"]["source_run_id"] for run in bundle["runs"]] == ["before", "after"]
    mixed = copy.deepcopy(bundle)
    mixed.pop("comparisons")
    mixed["runs"][1]["manifest"]["dataset_hash"] = "other-benchmark"
    with pytest.raises(ValueError, match="exactly one baseline/candidate pair"):
        build(mixed)
    mixed = copy.deepcopy(bundle)
    extra = copy.deepcopy(mixed["runs"][0])
    extra["id"] = "third"
    mixed["runs"].append(extra)
    with pytest.raises(ValueError, match="exactly two runs"):
        render(mixed, tmp_path / "invalid.html")
    assert not (tmp_path / "invalid.html").exists()


@pytest.mark.parametrize(
    "mismatch",
    [
        "corpus",
        "assigned",
        "evaluator",
        "input",
        "state",
        "input_data",
        "state_data",
        "shared",
    ],
)
def test_comparison_rejects_unrelated_cases_or_marks_unconfirmed_pairs(
    experiment: Comparison, mismatch: str
) -> None:
    bundle = experiment.bundle()
    candidate = bundle["runs"][1]
    if mismatch == "corpus":
        candidate["manifest"]["dataset_hash"] = "different"
    elif mismatch == "assigned":
        candidate["cases"].pop()
    elif mismatch == "evaluator":
        candidate["manifest"]["evaluation_profile_hash"] = "different"
    elif mismatch == "input_data":
        candidate["cases"][0]["input"]["question"] = "Different request"
    elif mismatch == "state_data":
        candidate["cases"][0]["state_snapshots"]["before"] = {"changed": True}
    elif mismatch == "shared":
        candidate["manifest"]["state_mode"] = "shared"
    else:
        candidate["cases"][0]["input_hash" if mismatch == "input" else "initial_state_hash"] = (
            "different"
        )
    if mismatch in {"corpus", "assigned"}:
        with pytest.raises(ValueError, match="Comparison requires the same"):
            comparison_rows(bundle)
    else:
        assert comparison_rows(bundle)[0]["change"] == "not comparable"


def test_baseline_adoption_preserves_evidence_and_rejects_stale_or_changed_runs(
    tmp_path: Path, experiment: Comparison
) -> None:
    reference, spec, report = (
        tmp_path / "current.json",
        tmp_path / "experiment.json",
        tmp_path / "report.html",
    )
    save_json(spec, experiment.model_dump())
    originals = {
        ref.path: Path(ref.path).read_bytes() for ref in (experiment.baseline, experiment.candidate)
    }
    assert (
        main(
            [
                "experiment",
                "baseline",
                "init",
                experiment.baseline.path,
                "--config",
                str(experiment.baseline.config_path),
                "--output",
                str(reference),
            ]
        )
        == 0
    )
    experiment.baseline = SavedRun.model_validate_json(reference.read_text())
    save_json(spec, experiment.model_dump(), overwrite=True)
    assert main(["experiment", "baseline", "check", str(reference)]) == 0
    assert main(["experiment", "compare", str(spec), "--output", str(report)]) == 0
    assert main(["experiment", "baseline", "accept", str(spec), "--output", str(reference)]) == 0
    assert SavedRun.model_validate_json(reference.read_text()) == experiment.candidate
    with pytest.raises(ValueError, match="baseline changed"):
        main(["experiment", "baseline", "accept", str(spec), "--output", str(reference)])
    for path, value in originals.items():
        assert Path(path).read_bytes() == value
    changed = json.loads(Path(experiment.candidate.path).read_text())
    changed["runs"][0]["cases"][0]["answer"] = "Replaced output"
    Path(experiment.candidate.path).write_text(json.dumps(changed))
    with pytest.raises(ValueError, match="Saved run changed"):
        experiment.bundle()


def test_old_source_cannot_be_adopted(tmp_path: Path, experiment: Comparison) -> None:
    path = tmp_path / "stale.json"
    bundle = experiment.candidate.load()
    bundle["runs"][0]["manifest"]["execution_hash"] = "0" * 64
    save_json(path, bundle)
    with pytest.raises(ValueError, match="current source"):
        main(
            [
                "experiment",
                "baseline",
                "init",
                str(path),
                "--config",
                str(experiment.candidate.config_path),
                "--output",
                str(tmp_path / "current.json"),
            ]
        )


def test_reused_source_run_ids_do_not_collide_in_comparison(
    tmp_path: Path, experiment: Comparison
) -> None:
    candidate = experiment.candidate.load()
    candidate["runs"][0]["id"] = experiment.baseline.load()["runs"][0]["id"]
    path = tmp_path / "reused-id.json"
    save_json(path, candidate)
    spec = experiment.model_copy(update={"candidate": SavedRun.freeze(path)})
    bundle = spec.bundle()
    assert [run["id"] for run in bundle["runs"]] == ["baseline", "candidate"]
    assert [run["manifest"]["source_run_id"] for run in bundle["runs"]] == ["before", "before"]
    assert comparison_rows(bundle)[0]["change"] == "improved"


def test_freshness_ignores_non_runtime_changes_but_checks_config_and_data(
    experiment: Comparison,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from dwelly_bot.experiments import comparison

    bundle = experiment.candidate.load()
    bundle["runs"][0]["manifest"].update(
        code_revision="0" * 64,
        source_changed_during_run=True,
        execution_changed_during_run=False,
    )
    path = tmp_path / "comments-only.json"
    save_json(path, bundle)
    ref = SavedRun.freeze(path, config_path=Path(str(experiment.candidate.config_path)))
    ref.require_current()
    monkeypatch.setattr(comparison, "dataset_hash", lambda _: "changed-corpus")
    with pytest.raises(ValueError, match="Dataset changed"):
        ref.require_current()
    monkeypatch.setattr(comparison, "dataset_hash", lambda _: "same-corpus")
    config_path = Path(str(ref.config_path))
    config = json.loads(config_path.read_text())
    config["model"] = "different-model"
    config_path.write_text(json.dumps(config))
    with pytest.raises(ValueError, match="configuration differs"):
        ref.require_current()


def test_execution_fingerprint_excludes_offline_changes_and_preserves_runtime_instructions(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from dwelly_bot.experiments import provenance

    monkeypatch.setattr(provenance, "ROOT", tmp_path)
    for name, value in {
        "src/dwelly_bot/harness/runtime.py": 'def tool():\n    """Read account."""\n    return 1\n',
        "src/dwelly_bot/reporting/assets/report.css": "body {}",
        "src/dwelly_bot/analysis/recipes.py": "VALUE = 1\n",
        "src/dwelly_bot/evaluation/checks.py": "VALUE = 1\n",
        "src/dwelly_bot/prompts/discovery-screen.md": "Find topics",
        "src/dwelly_bot/prompts/case-agent.md": "Resolve the case",
        "configs/baseline.toml": 'model = "original"',
        "pyproject.toml": '[project]\ndependencies = []\nrequires-python = ">=3.12"',
        "uv.lock": "version = 1",
        "LICENSE": "Fixture",
    }.items():
        path = tmp_path / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(value)
    before = provenance.execution_hash()
    bookkeeping = tmp_path / "src/dwelly_bot/experiments/comparison.py"
    bookkeeping.parent.mkdir()
    bookkeeping.write_text("BOOKKEEPING = 2\n")
    runtime = tmp_path / "src/dwelly_bot/harness/runtime.py"
    runtime.write_text('# Comment\n\ndef tool():\n    """Read account."""\n    return (1)\n')
    (tmp_path / "src/dwelly_bot/analysis/recipes.py").write_text("VALUE = 2\n")
    (tmp_path / "src/dwelly_bot/evaluation/checks.py").write_text("VALUE = 2\n")
    (tmp_path / "src/dwelly_bot/reporting/assets/report.css").write_text("body {color:red}")
    (tmp_path / "src/dwelly_bot/prompts/discovery-screen.md").write_text("Other analysis prompt")
    (tmp_path / "configs/baseline.toml").write_text('model = "changed"')
    assert provenance.execution_hash() == before  # Config is checked separately.
    runtime.write_text(runtime.read_text().replace("Read account.", "Close account."))
    assert provenance.execution_hash() != before
    runtime.write_text(runtime.read_text().replace("Close account.", "Read account."))
    prompt = tmp_path / "src/dwelly_bot/prompts/case-agent.md"
    prompt.write_text("Escalate the case")
    assert provenance.execution_hash() != before


def test_changed_evaluator_and_midrun_execution_cannot_be_adopted(
    experiment: Comparison,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from dwelly_bot.experiments import comparison

    monkeypatch.setattr(comparison, "evaluator_hash", lambda *_: "changed-evaluator")
    experiment.candidate.require_current()  # Evaluation changes do not invalidate execution.
    bundle = experiment.candidate.load()
    bundle["runs"][0]["manifest"]["execution_changed_during_run"] = True
    path = tmp_path / "mixed-execution.json"
    save_json(path, bundle)
    with pytest.raises(ValueError, match="current source"):
        SavedRun.freeze(
            path, config_path=Path(str(experiment.candidate.config_path))
        ).require_current()


async def test_experiment_runs_only_candidate_against_immutable_saved_baseline(
    tmp_path: Path,
    experiment: Comparison,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from dwelly_bot.experiments import comparison

    monkeypatch.setattr(comparison, "ROOT", tmp_path)
    # The working code and model differ from the baseline, intentionally.
    monkeypatch.setattr(comparison, "execution_hash", lambda *_: "new-code")
    config = tmp_path / "candidate-config.json"
    save_json(config, RunConfig(model="new-candidate-model").model_dump(mode="json"))
    reference = tmp_path / "accepted.json"
    save_json(reference, experiment.baseline.model_dump())
    original = Path(experiment.baseline.path).read_bytes()
    calls = []

    async def execute(dataset: str, settings: RunConfig, **kwargs: Any) -> Path:
        calls.append((dataset, settings, kwargs))
        assert settings.model == "new-candidate-model"
        assert kwargs["ids"] == ["0", "1", "2", "3"]
        return Path(experiment.candidate.path)

    monkeypatch.setattr(comparison, "execute", execute)
    argv = [
        "change",
        "--config",
        str(config),
        "--baseline",
        str(reference),
        "--description",
        "Change model",
    ]
    assert await comparison.run(argv) == 0
    assert len(calls) == 1
    assert Path(experiment.baseline.path).read_bytes() == original
    spec = Comparison.model_validate_json((tmp_path / "experiments/change/spec.json").read_text())
    assert spec.baseline == experiment.baseline
    published = tmp_path / "experiments/change"
    assert {p.name for p in published.iterdir()} == {
        "config.json",
        "spec.json",
        "results.json.gz",
        "comparison.html",
    }
    assert spec.candidate.load()["runs"] == experiment.candidate.load()["runs"]
    assert SavedRun.model_validate_json(reference.read_text()) == experiment.baseline

    monkeypatch.setattr(comparison, "dataset_hash", lambda _: "different-corpus")
    with pytest.raises(ValueError, match="Dataset differs"):
        await comparison.run(["other", *argv[1:]])
    reference.unlink()
    with pytest.raises(FileNotFoundError):
        await comparison.run(["missing", *argv[1:]])
    assert len(calls) == 1  # No fallback control or candidate execution.


def test_report_discovers_new_metrics_without_baseline_measurements(experiment: Comparison) -> None:
    bundle = experiment.bundle()
    old, new = [run["cases"][0] for run in bundle["runs"]]
    old["verifier"]["metrics"] = {"risk": {"value": 0.2, "version": "risk-v1"}}
    new["verifier"]["metrics"] = {"risk": {"value": 0.1, "version": "risk-v1"}, "new_metric": 0}
    new["verifier"]["red_flags"] = [{"id": "new_flag", "reason": "New detector"}]
    new["assessments"] = {"new_assessment": {"value": "review", "version": "v1"}}
    bundle["runs"][1]["manifest"]["evaluation_profile_hash"] = "new-evals"
    report = build(bundle)
    rows = next(b.data["rows"] for b in report.blocks if b.title == "Evaluation details")
    by_metric = {r["fields"]["Metric"]: r["fields"] for r in rows}
    assert by_metric["metric/risk"]["Delta"] == pytest.approx(-0.1)
    assert by_metric["metric/new_metric"]["Baseline"] == "not measured"
    assert by_metric["metric/new_metric"]["Experiment"] == 0
    assert by_metric["metric/new_metric"]["Delta"] is None
    assert by_metric["flag/new_flag"]["Experiment"] == "flagged"
    assert by_metric["assessment/new_assessment"]["Experiment"] == "review"
    new["verifier"]["metrics"]["risk"]["version"] = "risk-v2"
    report = build(bundle)
    rows = next(b.data["rows"] for b in report.blocks if b.title == "Evaluation details")
    assert (
        next(r for r in rows if r["fields"]["Metric"] == "metric/risk")["fields"]["Delta"] is None
    )


async def test_changed_evaluator_regrades_saved_baseline_without_running_it(
    tmp_path: Path,
    experiment: Comparison,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from dwelly_bot.experiments import comparison

    monkeypatch.setattr(comparison, "ROOT", tmp_path)
    monkeypatch.setattr(comparison, "evaluator_hash", lambda *_: "new-evaluator")
    monkeypatch.setattr(
        comparison,
        "grading_profile",
        lambda bundle, *_: bundle["runs"][0]["manifest"].update(
            evaluation_profile_hash="new-evaluator"
        ),
    )
    calls = []

    async def grade(bundle: dict[str, Any], *args: Any) -> tuple[dict[str, Any], None]:
        calls.append("evaluate-baseline")
        bundle["runs"][0]["cases"][0]["verifier"]["metrics"] = {"new_metric": 42}
        return bundle, None

    async def execute(*args: Any, **kwargs: Any) -> Path:
        calls.append("run-candidate")
        return Path(experiment.candidate.path)

    monkeypatch.setattr(comparison, "grade_bundle", grade)
    monkeypatch.setattr(comparison, "execute", execute)
    reference = tmp_path / "accepted.json"
    save_json(reference, experiment.baseline.model_dump())
    original = Path(experiment.baseline.path).read_bytes()
    await comparison.run(
        [
            "new-check",
            "--baseline",
            str(reference),
            "--config",
            str(experiment.candidate.config_path),
            "--description",
            "Add metric",
        ]
    )
    assert calls == ["evaluate-baseline", "run-candidate"]
    assert Path(experiment.baseline.path).read_bytes() == original
    spec = Comparison.model_validate_json(
        (tmp_path / "experiments/new-check/spec.json").read_text()
    )
    assert spec.baseline == experiment.baseline
    assert spec.bundle()["runs"][0]["cases"][0]["verifier"]["metrics"] == {"new_metric": 42}
    tampered = spec.candidate.load()
    regraded = tampered["baseline_evaluation"]
    regraded["runs"][0]["cases"][0]["batch_result"] = {"type": "succeeded"}
    batch = tmp_path / "batch-judged.json"
    save_json(batch, tampered)
    assert spec.model_copy(update={"candidate": SavedRun.freeze(batch)}).bundle()
    regraded["runs"][0]["cases"][0]["answer"] = "Replaced answer"
    altered = tmp_path / "tampered.json"
    save_json(altered, tampered)
    with pytest.raises(ValueError, match="execution evidence"):
        spec.model_copy(update={"candidate": SavedRun.freeze(altered)}).bundle()


def test_failed_preparation_does_not_discard_the_baseline(experiment: Comparison) -> None:
    from dwelly_bot.experiments.comparison import require_evidence

    bundle = experiment.bundle()
    control = bundle["runs"][0]
    case = control["cases"][0]
    case.update(
        execution_status="error", initial_state_hash=None, state_snapshots={}, tool_events=[]
    )
    require_evidence(control)
    assert comparison_rows(bundle)[0]["change"] == "not comparable"
    case["input"]["question"] = "Tampered input"
    with pytest.raises(ValueError, match="provenance"):
        require_evidence(control)


def test_large_report_payload_round_trips_without_network() -> None:
    import base64
    import gzip

    from dwelly_bot.reporting.page import document

    data = {"text": "<script>untrusted</script>" * 50000}
    html = document("report", "Large evidence", data)
    encoded = json.loads(
        html.split('<script id="report-data" type="application/json">')[1].split("</script>")[0]
    )
    assert encoded["encoding"] == "gzip-base64"
    assert json.loads(gzip.decompress(base64.b64decode(encoded["data"]))) == data
    assert len(html) < len(data["text"])


def test_continuation_retains_failed_attempts_and_rejects_changed_conditions(
    tmp_path: Path,
) -> None:
    from dwelly_bot.evaluation import attempts
    from dwelly_bot.reporting.resources import summarize

    first, second = tmp_path / "first.json", tmp_path / "second.json"
    original = saved(first, "first", [False, True])
    old = original["runs"][0]["cases"][0]
    old.update(execution_status="error", error="BudgetExceeded: local allowance")
    old["metrics"] = {"cost_usd": 0.2, "latency_ms": 1000}
    save_json(first, original, overwrite=True)
    retry = saved(second, "retry", [True])
    retry["runs"][0]["cases"][0]["metrics"] = {"cost_usd": 0.1, "latency_ms": 2000}
    retry["runs"][0]["manifest"]["resolved_config"]["total_budget_usd"] = 20
    save_json(second, retry, overwrite=True)
    combined = attempts.combine([first, second])["runs"][0]
    assert len(combined["cases"]) == 2
    case = combined["cases"][0]
    assert case["verifier"]["goal_pass"] is True
    assert case["previous_attempts"][0]["verifier"]["goal_pass"] is False
    assert summarize([case])["cost_usd"] == pytest.approx(0.3)
    assert summarize([case])["cumulative_case_seconds"] == 3
    retry["runs"][0]["manifest"]["resolved_config"]["model"] = "changed"
    save_json(second, retry, overwrite=True)
    with pytest.raises(ValueError, match="preserve isolated runtime"):
        attempts.combine([first, second])
    retry["runs"][0]["manifest"]["resolved_config"]["model"] = RunConfig().model
    save_json(second, retry, overwrite=True)
    old["error"] = "Ordinary model failure"
    save_json(first, original, overwrite=True)
    with pytest.raises(ValueError, match="Only budget-blocked"):
        attempts.combine([first, second])
