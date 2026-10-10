# SPDX-License-Identifier: Apache-2.0
"""Offline contract tests. Scripted SDK responses are not model-quality evidence."""

import asyncio
import copy
import json
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any, cast

import pytest
from pydantic_ai import ModelResponse, ToolCallPart
from pydantic_ai.messages import ModelMessage
from pydantic_ai.models.function import AgentInfo, FunctionModel

from dwelly_bot.budget import BudgetLedger
from dwelly_bot.contracts import RunConfig, SolutionOutput
from dwelly_bot.evaluation.calibration import compare
from dwelly_bot.evaluation.checks import hard_checks
from dwelly_bot.evaluation.judge import ROOT, LlmJudge
from dwelly_bot.evaluation.runner import evaluate_bundle, evaluation_status
from dwelly_bot.experiments.bundle import validate
from dwelly_bot.experiments.cli import main as experiment
from dwelly_bot.experiments.journal import Journal, capture_case, recover_events
from dwelly_bot.harness.runtime import CaseRuntime
from dwelly_bot.reporting.html import render
from dwelly_bot.storage import fingerprint

REQUEST_CONTRACT = {
    "goal_contract_complete": True,
    "checks": [
        {
            "id": "goal",
            "kind": "goal",
            "label": "Request to the right customer is recorded",
            "path": "/state_snapshots/after/request_for_target_sent",
            "equals": True,
        }
    ],
}


def structured_response(info: AgentInfo, payload: dict[str, Any]) -> ModelResponse:
    return ModelResponse([ToolCallPart(info.output_tools[0].name, payload)])


def judge_response(info: AgentInfo, rubric: dict[str, Any], evidence: list[str]) -> ModelResponse:
    return structured_response(
        info,
        {
            "summary": "Scripted SDK fixture",
            "findings": [
                {
                    "criterion": c["id"],
                    "status": "pass",
                    "reason": "Scripted evidence check",
                    "evidence_ids": evidence,
                }
                for c in rubric["criteria"]
            ],
        },
    )


def probes() -> list[dict[str, Any]]:
    return cast(
        list[dict[str, Any]],
        json.loads((Path(__file__).parent / "fixtures/judge-calibration.json").read_text()),
    )


@pytest.mark.parametrize(
    "schema,assigned,cases",
    [
        (1, ["case"], []),
        (True, ["case"], []),
        (1, "case", []),
        (1, ["case"], {}),
        (1, ["case", "case"], []),
        (1, ["case"], [{"id": 1}]),
    ],
)
def test_saved_bundle_boundary_preserves_denominator_or_rejects_invalid_data(
    schema: Any, assigned: Any, cases: Any
) -> None:
    bundle = {
        "schema_version": schema,
        "runs": [{"id": "run", "manifest": {"assigned_case_ids": assigned}, "cases": cases}],
    }
    if schema is True or assigned != ["case"] or cases != []:
        with pytest.raises(ValueError):
            validate(bundle)
    else:
        assert validate(bundle)["runs"][0]["cases"][0]["execution_status"] == "missing_result"


async def test_pydantic_subject_messages_and_tool_journal(tmp_path: Path) -> None:
    calls: list[int] = []

    def scripted(messages: list[ModelMessage], info: AgentInfo) -> ModelResponse:
        calls.append(1)
        if len(calls) == 1:
            return ModelResponse([ToolCallPart("send", {"customer_id": "A"})])
        return structured_response(
            info,
            {
                "answer": "Request sent.",
                "public_rationale": "Receipt R1 was returned.",
                "agent_disposition": "completed",
            },
        )

    journal = Journal(tmp_path / "tools.jsonl")
    runtime = CaseRuntime(FunctionModel(scripted), RunConfig(), journal)

    async def send(customer_id: str) -> dict[str, Any]:
        return {"receipt": "R1", "customer_id": customer_id}

    agent = runtime.agent(
        output_type=SolutionOutput,
        output_name="resolve_case",
        tools=[runtime.tool("send", "Send request", send)],
        instructions="Scripted plumbing check",
    )
    result = await runtime.ask(agent, {"task": "Synthetic plumbing check"})
    journal.close()
    assert result.output.answer == "Request sent."
    assert len(journal.events) == 1
    assert journal.events[0]["role"] == "subject"
    assert runtime.role_records[0]["messages"]
    assert result.usage.requests == 2


async def test_write_ahead_and_unconfirmed_recovery(tmp_path: Path) -> None:
    path = tmp_path / "tools.jsonl"
    journal = Journal(path)
    effects: list[str] = []

    async def invoke(customer_id: str) -> dict[str, Any]:
        first = json.loads(path.read_text().splitlines()[0])
        assert first["status"] == "started"
        effects.append(customer_id)
        return {"receipt": "R1"}

    await journal.call("send", {"customer_id": "A"}, invoke, intent="Request missing document")
    journal.append({"id": "lost", "tool": "other", "status": "started"})
    journal.close()
    events = recover_events(path)
    assert effects == ["A"]
    assert events[0]["intent"] == "Request missing document"
    assert events[0]["result"] == {"receipt": "R1"}
    assert events[1]["status"] == "unconfirmed"


async def test_verified_effect_survives_subject_failure(tmp_path: Path) -> None:
    case = probes()[0]["case"]
    state = {"request_for_target_sent": False}

    async def subject(inputs: dict[str, Any], journal: Journal) -> dict[str, Any]:

        async def send() -> dict[str, Any]:
            state["request_for_target_sent"] = True
            raise RuntimeError("Acknowledgement was lost")

        await journal.call("send", {}, send)
        raise AssertionError("Expected the transport error")

    captured = await capture_case(case, tmp_path / "case", subject, lambda: copy.deepcopy(state))
    assert captured["execution_status"] == "error"
    assert len(captured["tool_events"]) == 1
    grade = hard_checks(captured, REQUEST_CONTRACT)
    assert grade["goal_pass"]
    assert grade["checks"][-1]["status"] == "pass"


async def test_missing_evidence_unknown_not_pass() -> None:
    case = copy.deepcopy(probes()[0]["case"])
    case["state_snapshots"] = {}
    grade = hard_checks(case, REQUEST_CONTRACT)
    assert grade["goal_pass"] is None
    assert grade["checks"][0]["status"] == "unknown"
    bad = {"checks": [{"id": "claim", "kind": "goal", "path": "/answer/summary", "equals": "done"}]}
    with pytest.raises(ValueError):
        hard_checks(case, bad)


@pytest.mark.parametrize("broken", [None, "verifier", "judge"])
async def test_real_pydantic_evals_and_typed_judge(tmp_path: Path, broken: str | None) -> None:
    rubric = json.loads((ROOT / "rubrics/default.json").read_text())

    def scripted(messages: list[ModelMessage], info: AgentInfo) -> ModelResponse:
        return judge_response(
            info, rubric, ["INVENTED"] if broken == "judge" else ["TASK", "ANSWER"]
        )

    judge = LlmJudge(FunctionModel(scripted), rubric)
    case = copy.deepcopy(probes()[0]["case"])
    case.update(judge_error="STALE_ERROR", judge_metrics={"old_cost": 99})
    case["state_snapshots"] = {"before": {}, "after": {"request_for_target_sent": True}}
    case["evaluation_contract"] = copy.deepcopy(REQUEST_CONTRACT)
    if broken == "verifier":
        case["evaluation_contract"]["checks"][0]["path"] = "/answer"
    case["input_hash"] = fingerprint(case["input"])
    case["initial_state_hash"] = fingerprint(case["state_snapshots"]["before"])
    bundle: dict[str, Any] = {
        "schema_version": 1,
        "runs": [
            {
                "id": "test",
                "label": "Scripted plumbing test",
                "manifest": {
                    "assigned_case_ids": [case["id"], "missing"],
                    "dataset_hash": "test",
                    "environment_version": "test",
                    "state_mode": "isolated",
                },
                "cases": [case],
            }
        ],
    }
    graded, native = await evaluate_bundle(bundle, judge=judge, judge_name="scripted-not-a-model")
    good, missing = graded["runs"][0]["cases"]
    assert good["verifier"]["goal_pass"] is (None if broken == "verifier" else True)
    assert good["judge_status"] == ("error" if broken == "judge" else "available")
    assert evaluation_status(graded) == int(broken is not None)
    if broken == "judge":
        assert "INVENTED" in json.dumps(good["judge_record"])
    else:
        assert "judge_error" not in good and "old_cost" not in good["judge_metrics"]
        assert len(good["judge"]) == 3
    assert good["tool_events"] == case["tool_events"]
    assert missing["execution_status"] == "missing_result"
    assert missing["verifier"]["goal_pass"] is None
    assert len(native[0]["cases"]) == 2
    assert "evaluation_profile" not in bundle["runs"][0]["manifest"]
    output = tmp_path / "report.html"
    render(graded, output)
    assert "Scripted plumbing test" in output.read_text()
    source, destination = tmp_path / "capture.json", tmp_path / "graded.json"
    source.write_text(json.dumps(bundle))
    assert await asyncio.to_thread(
        experiment, ["evaluate", "--input", str(source), "--output", str(destination)]
    ) == int(broken == "verifier")
    assert "Evaluation error" in destination.with_suffix(".html").read_text()
    if broken != "verifier":
        assert "check/goal" in native[0]["cases"][0]["labels"]


async def test_calibration_does_not_drop_missing_predictions(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    examples = probes()[:2]
    pred = {
        examples[0]["case"]["id"]: {
            "status": "available",
            "findings": [{"criterion": k, "status": "fail"} for k in examples[0]["expected"]],
        }
    }
    result = compare(pred, examples)
    assert result["expected_checks"] == 5
    assert result["false_accusations"] == 3
    assert result["missing_predictions"] == 2
    from dwelly_bot.evaluation.calibration import main as calibrate

    @asynccontextmanager
    async def configured(*args: Any) -> AsyncIterator[tuple[LlmJudge, RunConfig]]:
        rubric = args[1]
        yield (
            LlmJudge(FunctionModel(lambda _, info: judge_response(info, rubric, ["TASK"])), rubric),
            RunConfig(model="scripted-judge"),
        )

    monkeypatch.setattr("dwelly_bot.evaluation.paid.judge_context", configured)
    source, repeated = tmp_path / "calibration.json", tmp_path / "repeated.json"
    cases = str(Path(__file__).parent / "fixtures/judge-calibration.json")
    assert (
        await calibrate(["--cases", cases, "--judge-config", "fixture", "--output", str(source)])
        == 0
    )
    assert (
        await calibrate(["--cases", cases, "--predictions", str(source), "--output", str(repeated)])
        == 0
    )
    first, second = json.loads(source.read_text()), json.loads(repeated.read_text())
    assert first["judge_model"] == second["judge_model"] == "scripted-judge"
    assert first["profile_hash"] == second["profile_hash"]
    assert first["comparison"] == second["comparison"]


@pytest.mark.parametrize("conflict", ["html", "json"])
async def test_grading_rejects_output_collisions_before_work(tmp_path: Path, conflict: str) -> None:
    from dwelly_bot.evaluation.runner import main as evaluate

    source, output = tmp_path / "capture.json", tmp_path / "graded.json"
    source.write_text("{}")
    arguments = [
        "--input",
        str(source),
        "--output",
        str(output if conflict != "html" else tmp_path / "graded.html"),
    ]
    if conflict == "json":
        arguments += ["--html", str(source)]
    with pytest.raises(SystemExit) as error:
        await evaluate(arguments)
    assert error.value.code == 2 and source.read_text() == "{}" and not output.exists()


def test_settlement_is_idempotent_and_terminal(tmp_path: Path) -> None:
    ledger = BudgetLedger(tmp_path / "budget.json", 1)
    token, account = ledger.reserve_account(0.2, "fixture", "A", {"account": 1})
    assert account == "account"
    ledger.uncertain(token)
    assert ledger.summary()["exposure_usd"] == 0.2
    ledger.settle(token, 0.1, "provider_reported", "receipt")
    ledger.settle(token, 0.1, "provider_reported", "receipt")
    for amount, receipt in [(0.05, "receipt"), (0.1, "other")]:
        with pytest.raises(ValueError, match="Conflicting settlement"):
            ledger.settle(token, amount, "provider_reported", receipt)
    with pytest.raises(ValueError, match="cannot become uncertain"):
        ledger.uncertain(token)
    summary = ledger.summary()
    assert summary["reported_cost_usd"] == summary["exposure_usd"] == 0.1
    assert summary["accounts"] == {"account": 0.1}
    assert summary["uncertain_requests"] == summary["pending_requests"] == 0


async def test_judge_concurrency_is_bounded_and_one_failure_does_not_drop_cases(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    rubric = json.loads((ROOT / "rubrics/default.json").read_text())
    judge = LlmJudge(
        FunctionModel(lambda messages, info: judge_response(info, rubric, ["TASK"])), rubric
    )
    original_review = judge.review
    active = peak = 0

    async def review(case: dict[str, Any]) -> dict[str, Any]:
        nonlocal active, peak
        active += 1
        peak = max(peak, active)
        try:
            await asyncio.sleep(0.01)
            if case["id"] == "0":
                raise ValueError("One judge failed")
            return await original_review(case)
        finally:
            active -= 1

    monkeypatch.setattr(judge, "review", review)
    cases = [{**copy.deepcopy(probes()[0]["case"]), "id": str(i)} for i in range(12)]
    bundle = {
        "schema_version": 1,
        "runs": [
            {
                "id": "bounded-judge",
                "manifest": {"assigned_case_ids": [c["id"] for c in cases]},
                "cases": cases,
            }
        ],
    }
    graded, _ = await evaluate_bundle(bundle, judge=judge, concurrency=3)
    rows = graded["runs"][0]["cases"]
    assert peak == 3 and active == 0
    assert [c["id"] for c in rows] == [c["id"] for c in cases]
    assert rows[0]["judge_status"] == "error"
    assert all(c["judge_status"] == "available" for c in rows[1:])


async def test_failures_require_review_but_diagnostics_stay_local(tmp_path: Path) -> None:
    from dwelly_bot.reporting.submission import export

    async def subject(inputs: dict[str, Any], journal: Journal) -> dict[str, Any]:
        def broken_tool() -> None:
            raise ValueError("Fixture tool failure")

        await journal.call("broken_tool", {}, broken_tool)
        return {}

    case = await capture_case({"id": "A", "input": {}}, tmp_path / "case", subject)
    assert "broken_tool" in case["error_traceback"]
    assert "ValueError: Fixture tool failure" in case["tool_events"][0]["error"]["traceback"]
    bundle = {
        "schema_version": 1,
        "runs": [
            {
                "id": "error",
                "manifest": {"assigned_case_ids": ["A"]},
                "cases": [case],
            }
        ],
    }
    export(bundle, tmp_path / "ANSWERS")
    exported = tmp_path / "ANSWERS/1"
    assert not (exported / "STACKTRACE.txt").exists()
    assert "requires human review" in (exported / "ANSWER.md").read_text()
    assert case["execution_status"] == "error" and case["agent_disposition"] == "escalated"
    for path in exported.iterdir():
        content = path.read_text()
        assert "traceback" not in content and "Fixture tool failure" not in content
    assert "Fixture tool failure" in (tmp_path / "case/execution.json").read_text()
