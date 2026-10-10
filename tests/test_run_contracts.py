"""Execution contracts: fair comparisons, bounded spending and truthful recovery/export."""

import asyncio
import json
from pathlib import Path
from typing import Any, Literal

import pytest
from pydantic import ValidationError
from pydantic_ai import Agent, ModelResponse, ToolCallPart, ToolReturnPart
from pydantic_ai.messages import ModelMessage, TextPart
from pydantic_ai.models.function import AgentInfo, FunctionModel
from pydantic_ai.usage import RequestUsage

from dwelly_bot.budget import BudgetExceeded, BudgetLedger
from dwelly_bot.cli import main
from dwelly_bot.contracts import AgentCase, ModelProfile, RunConfig, SolutionOutput
from dwelly_bot.evaluation.batch import apply_results, prepare
from dwelly_bot.evaluation.checks import hard_checks, pointer
from dwelly_bot.evaluation.judge import ROOT as JUDGE_ROOT
from dwelly_bot.evaluation.saved import grade_bundle
from dwelly_bot.experiments.agent import RunFailure, capture_cases, execute
from dwelly_bot.experiments.journal import Journal
from dwelly_bot.harness.policy import PolicyGate, RiskRule
from dwelly_bot.harness.runtime import CaseRuntime
from dwelly_bot.models import BudgetedModel
from dwelly_bot.providers import ModelPool, credentials
from dwelly_bot.reporting.submission import export
from dwelly_bot.storage import load_json, save_json


def answer(messages: list[ModelMessage], info: AgentInfo) -> ModelResponse:
    return ModelResponse(
        [
            ToolCallPart(
                info.output_tools[0].name,
                {
                    "answer": "Observed result",
                    "public_rationale": "Scripted fixture",
                    "agent_disposition": "completed",
                },
            )
        ],
        usage=RequestUsage(input_tokens=10, output_tokens=10),
        provider_details={"cost": 0.02},
    )


def bundle(ids: list[str]) -> dict[str, Any]:
    return {
        "schema_version": 1,
        "runs": [
            {
                "id": "fixture",
                "manifest": {
                    "assigned_case_ids": ids,
                    "state_mode": "isolated",
                    "dataset_hash": "fixture",
                    "environment_version": "fixture",
                },
                "cases": [],
            }
        ],
    }


def test_explicit_budget_and_credential_contract(monkeypatch: pytest.MonkeyPatch) -> None:
    with pytest.raises(ValidationError):
        RunConfig(total_budget_usd=400)
    assert (
        RunConfig(
            total_budget_usd=400, budget_file="experiments/event/artifacts/budget.json"
        ).total_budget_usd
        == 400
    )
    with pytest.raises(ValidationError):
        ModelProfile(provider="anthropic", model="fixture")
    monkeypatch.setenv("TEAM_KEY_A", "a-secret")
    monkeypatch.setenv("TEAM_KEY_B", "b-secret")
    profile = ModelProfile(key_envs=["TEAM_KEY_A", "TEAM_KEY_B"])
    assert credentials(profile) == {"TEAM_KEY_A": "a-secret", "TEAM_KEY_B": "b-secret"}
    assert "a-secret" not in profile.model_dump_json()


async def test_pool_rotates_with_persistent_account_allowances(tmp_path: Path) -> None:
    counts = {"a": 0, "b": 0}

    def model(name: str) -> FunctionModel:
        def respond(messages: list[ModelMessage], info: AgentInfo) -> ModelResponse:
            counts[name] += 1
            return answer(messages, info)

        return FunctionModel(respond)

    profile = ModelProfile(account_budget_usd=0.06)
    pool = ModelPool({"a": model("a"), "b": model("b")}, [], profile)
    ledger = BudgetLedger(tmp_path / "ledger.json", 1)
    bounded = BudgetedModel(pool, ledger, "case", profile=profile)
    agent = Agent(bounded, output_type=SolutionOutput, model_settings={"max_tokens": 256})
    for _ in range(6):
        await agent.run("fixture")
    assert counts == {"a": 3, "b": 3}
    with pytest.raises(BudgetExceeded):
        await agent.run("fixture")
    assert ledger.summary()["accounts"] == {"a": 0.06, "b": 0.06}
    assert "secret" not in ledger.path.read_text()


async def test_rejected_credential_fails_over_without_losing_exposure(tmp_path: Path) -> None:
    class AuthenticationError(Exception):
        pass

    def rejected(messages: list[ModelMessage], info: AgentInfo) -> ModelResponse:
        raise AuthenticationError("Secret must not appear in capture")

    profile = ModelProfile()
    pool = ModelPool({"a": FunctionModel(rejected), "b": FunctionModel(answer)}, [], profile)
    ledger = BudgetLedger(tmp_path / "ledger.json")
    bounded = BudgetedModel(pool, ledger, "fixture", profile=profile)
    result = await Agent(bounded, output_type=SolutionOutput).run("fixture")
    assert result.output.answer == "Observed result"
    assert [c["status"] for c in bounded.calls] == ["uncertain", "settled"]
    assert ledger.summary()["uncertain_requests"] == 1
    assert "Secret" not in ledger.path.read_text()


def test_missing_snapshot_cannot_prove_an_absence_goal() -> None:
    contract: dict[str, Any] = {
        "goal_contract_complete": True,
        "checks": [
            {
                "id": "absence",
                "kind": "goal",
                "path": "/state_snapshots/after/forbidden_change",
                "exists": False,
            }
        ],
    }
    assert hard_checks({}, contract)["goal_pass"] is None
    assert hard_checks({"state_snapshots": {"after": {}}}, contract)["goal_pass"] is True
    with pytest.raises(ValueError, match="unique"):
        hard_checks({}, {"checks": [contract["checks"][0], contract["checks"][0]]})


class FakeSession:
    def __init__(self, case: AgentCase, *, delay: float = 0.01) -> None:
        self.case, self.delay, self.done = case, delay, False

    async def run(self, runtime: CaseRuntime) -> SolutionOutput:
        await asyncio.sleep(self.delay)
        self.done = True
        return SolutionOutput(answer=self.case.id, public_rationale="Scripted fixture")

    def snapshot(self) -> dict[str, Any]:
        return {"done": self.done}

    def grade(self, execution: dict[str, Any]) -> dict[str, Any]:
        return {"status": "available", "goal_pass": execution["state_snapshots"]["after"]["done"]}


class FakeAdapter:
    name = "fixture"
    dataset_root = Path(".")
    state_mode: Literal["static", "isolated"] = "isolated"

    def __init__(self, cases: list[AgentCase], delay: float = 0.01) -> None:
        self.cases, self.delay, self.prepared = cases, delay, 0

    def load_cases(self, root: Path, ids: list[str] | None = None) -> list[AgentCase]:
        return self.cases

    def prepare(self, case: AgentCase, root: Path, config: RunConfig) -> FakeSession:
        self.prepared += 1
        return FakeSession(case, delay=self.delay)

    def grade_saved(
        self, case: AgentCase, root: Path, config: RunConfig, execution: dict[str, Any]
    ) -> dict[str, Any]:
        return self.prepare(case, root, config).grade(execution)


@pytest.mark.parametrize("ids", [["A", "A"], ["B", "A"]])
async def test_invalid_assignment_cannot_start_execution(tmp_path: Path, ids: list[str]) -> None:
    cases = [AgentCase(cid, "fixture", cid, {}) for cid in ids]
    adapter = FakeAdapter(cases)
    with pytest.raises(ValueError, match="unique assigned"):
        await capture_cases(
            adapter,
            tmp_path,
            cases,
            RunConfig(),
            FunctionModel(answer),
            BudgetLedger(tmp_path / "ledger.json"),
            tmp_path / "run",
            bundle(["A", "B"]),
        )
    assert adapter.prepared == 0 and not (tmp_path / "run").exists()


async def test_preparation_error_retains_assigned_cases_and_report(tmp_path: Path) -> None:
    class BrokenAdapter(FakeAdapter):
        def prepare(self, case: AgentCase, root: Path, config: RunConfig) -> FakeSession:
            if case.id == "bad":
                raise ValueError("Malformed case")
            return super().prepare(case, root, config)

    cases = [AgentCase(cid, "fixture", cid, {}) for cid in ["bad", "good"]]
    captured = await capture_cases(
        BrokenAdapter(cases),
        tmp_path,
        cases,
        RunConfig(),
        FunctionModel(answer),
        BudgetLedger(tmp_path / "ledger.json"),
        tmp_path,
        bundle([c.id for c in cases]),
    )
    assert [row["execution_status"] for row in captured["runs"][0]["cases"]] == [
        "error",
        "completed",
    ]
    assert "Malformed case" in captured["runs"][0]["cases"][0]["error"]
    assert (tmp_path / "results.json.gz").is_file()


async def test_capture_failure_propagates_and_finalizes_remaining_cases(tmp_path: Path) -> None:
    cases = [
        AgentCase("bad", "fixture", "bad", {}),
        AgentCase("peer", "fixture", "peer", {}),
    ]
    directory = tmp_path / "run"
    directory.mkdir()
    (directory / "0001").symlink_to(directory / "missing")
    captured = bundle([case.id for case in cases])
    with pytest.raises(ExceptionGroup):
        await capture_cases(
            FakeAdapter(cases, delay=0.2),
            tmp_path,
            cases,
            RunConfig(case_concurrency=2),
            FunctionModel(answer),
            BudgetLedger(tmp_path / "ledger.json"),
            directory,
            captured,
        )
    saved = load_json(directory / "results.json.gz")
    assert len(saved["runs"][0]["cases"]) == 2
    assert all(
        row["execution_status"] in {"not_started", "cancelled"} for row in saved["runs"][0]["cases"]
    )


@pytest.mark.parametrize(
    "invalid",
    [
        {"status": "available", "goal_pass": "true"},
        {"status": "error", "goal_pass": True},
        {"status": "available", "checks": [{"name": "old", "passed": True}]},
        {"status": "available", "checks": [{"id": "saved_execution_completed", "status": "pass"}]},
    ],
)
async def test_invalid_independent_verification_is_a_visible_error(
    tmp_path: Path, invalid: dict[str, Any]
) -> None:
    class InvalidAdapter(FakeAdapter):
        def grade_saved(
            self, case: AgentCase, root: Path, config: RunConfig, execution: dict[str, Any]
        ) -> dict[str, Any]:
            return invalid

    case = AgentCase("A", "fixture", "A", {})
    captured = bundle([case.id])
    captured["runs"][0]["manifest"].pop("dataset_hash")
    captured["runs"][0]["cases"] = [{"id": case.id, "input": {}, "execution_status": "completed"}]
    graded, _ = await grade_bundle(captured, tmp_path, InvalidAdapter([case]), RunConfig())
    verifier = graded["runs"][0]["cases"][0]["verifier"]
    assert verifier["status"] == "error" and verifier["goal_pass"] is None
    assert "Invalid verifier contract" in verifier["reason"]


@pytest.mark.parametrize("static", [False, True])
async def test_resume_restarts_only_incomplete_static_cases(
    tmp_path: Path,
    static: bool,
) -> None:
    cases = [AgentCase(str(i), "fixture", str(i), {"goal": "fixture"}) for i in range(3)]

    class StaticAdapter(FakeAdapter):
        state_mode = "static"

    adapter = (StaticAdapter if static else FakeAdapter)(cases, delay=0.2)
    run = bundle([c.id for c in cases])
    directory = tmp_path / "run"
    directory.mkdir()
    ledger = BudgetLedger(tmp_path / "ledger.json")
    config = RunConfig(case_concurrency=1, run_timeout_seconds=0.05)
    await capture_cases(
        adapter, tmp_path, cases, config, FunctionModel(answer), ledger, directory, run
    )
    assert [c["execution_status"] for c in run["runs"][0]["cases"]] == [
        "cancelled",
        "not_started",
        "not_started",
    ]
    adapter.delay = 0
    await capture_cases(
        adapter, tmp_path, cases, config, FunctionModel(answer), ledger, directory, run
    )
    assert adapter.prepared == (4 if static else 3)
    first = run["runs"][0]["cases"][0]
    if static:
        assert first["execution_status"] == "completed"
        assert first["previous_attempts"][0]["execution_status"] == "cancelled"
        await capture_cases(
            adapter, tmp_path, cases, config, FunctionModel(answer), ledger, directory, run
        )
        assert adapter.prepared == 4
        assert len(run["runs"][0]["cases"][0]["previous_attempts"]) == 1
    assert load_json(directory / "results.json.gz")["runs"][0]["cases"] == run["runs"][0]["cases"]
    assert json.loads((directory / "status.json").read_text())["assigned"] == 3


@pytest.mark.parametrize("static", [False, True])
async def test_crash_recovery_replays_only_static_cases(tmp_path: Path, static: bool) -> None:
    cases = [AgentCase("A", "fixture", "A", {"goal": "fixture"})]
    directory = tmp_path / "run"
    (directory / "0001").mkdir(parents=True)
    (directory / "0001/tools.jsonl").write_text(
        json.dumps({"id": "T1", "tool": "send", "status": "started"}) + "\n"
    )
    adapter = FakeAdapter(cases)
    adapter.state_mode = "static" if static else "isolated"
    run = bundle(["A"])
    await capture_cases(
        adapter,
        tmp_path,
        cases,
        RunConfig(),
        FunctionModel(answer),
        BudgetLedger(tmp_path / "ledger.json"),
        directory,
        run,
    )
    assert adapter.prepared == int(static)
    row = run["runs"][0]["cases"][0]
    assert row["execution_status"] == ("completed" if static else "unconfirmed")
    previous = row["previous_attempts"][0] if static else row
    assert previous["tool_events"][0]["status"] == "unconfirmed"


async def test_policy_write_guard_is_recorded_and_cannot_be_disabled(tmp_path: Path) -> None:
    journal = Journal(tmp_path / "tools.jsonl")
    runtime = CaseRuntime(FunctionModel(answer), RunConfig(), journal)
    runtime.policy_gate = PolicyGate(
        {"message": "Gas leak"},
        [
            RiskRule(
                id="urgent", terms=["gas leak"], handling="human_review", reason="Reviewed policy"
            )
        ],
    )
    effects: list[str] = []

    def book() -> dict[str, Any]:
        effects.append("booked")
        return {"ok": True}

    with pytest.raises(ValueError, match="human review"):
        invoke: Any = runtime.tool("book", "fixture", book).function
        await invoke()
    journal.close()
    assert effects == []
    assert journal.events[0]["status"] == "error"
    assert runtime.policy_gate.classify()["unmatched_is_safe"] is False


def test_shared_world_requires_sequential_cases() -> None:
    with pytest.raises(ValidationError, match="sequential"):
        RunConfig(environment_state_mode="shared", case_concurrency=2)


def test_export_preserves_failures_and_excludes_private_model_transcripts(tmp_path: Path) -> None:
    saved = bundle(["A", "B"])
    saved["runs"][0]["cases"] = [
        {
            "id": "A",
            "execution_status": "error",
            "answer": "Original failed output",
            "error": "Timeout",
            "model_messages": ["PRIVATE"],
        }
    ]
    export(saved, tmp_path / "ANSWERS")
    assert (tmp_path / "ANSWERS/1/ANSWER.md").read_text() == "Original failed output\n"
    assert "Timeout" not in (tmp_path / "ANSWERS/1/REASONING.md").read_text()
    assert (tmp_path / "ANSWERS/2/ANSWER.md").exists()
    assert "PRIVATE" not in (tmp_path / "ANSWERS/1/trace.json").read_text()
    with pytest.raises(ValueError):
        export(saved, tmp_path / "ANSWERS")


def test_batch_prepare_and_validation_keeps_ids_errors_and_independent_grades(
    tmp_path: Path,
) -> None:
    config = tmp_path / "config.json"
    config.write_text(
        json.dumps(
            {
                "provider": "anthropic",
                "model": "fixture",
                "input_price_per_million": 2,
                "output_price_per_million": 8,
            }
        )
    )
    saved = bundle(["A", "B"])
    saved["runs"][0]["cases"] = [
        {
            "id": cid,
            "input": {"request": "fixture"},
            "answer": "fixture",
            "execution_status": "completed",
            "verifier": {"goal_pass": False},
        }
        for cid in ["A", "B"]
    ]
    rubric = json.loads((JUDGE_ROOT / "rubrics/default.json").read_text())
    prepare(saved, config, tmp_path / "batch", rubric)
    job = json.loads((tmp_path / "batch/job.json").read_text())
    review = {
        "summary": "fixture",
        "findings": [
            {"criterion": c["id"], "status": "pass", "reason": "fixture", "evidence_ids": ["TASK"]}
            for c in rubric["criteria"]
        ],
    }
    results = [
        {
            "custom_id": job["items"][0]["custom_id"],
            "result": {
                "type": "succeeded",
                "message": {
                    "content": [{"type": "tool_use", "name": "submit_review", "input": review}],
                    "usage": {"input_tokens": 10, "output_tokens": 20},
                },
            },
        },
        {"custom_id": job["items"][1]["custom_id"], "result": {"type": "expired"}},
    ]
    for case in job["bundle"]["runs"][0]["cases"]:
        case.update(judge_summary="STALE_SUMMARY", judge_metrics={"old_cost": 99})
    output = apply_results(job, results)
    a, b = output["runs"][0]["cases"]
    assert a["judge_status"] == "available" and a["verifier"]["goal_pass"] is False
    assert b["judge_status"] == "error" and "expired" in b["judge_error"]
    assert "judge_error" not in a and a["judge_metrics"]["output_tokens"] == 20
    assert "judge_summary" not in b and "judge_metrics" not in b
    results[0]["result"]["message"]["content"][0]["input"]["findings"][0]["evidence_ids"] = [
        "invented"
    ]
    invalid = apply_results(job, results)["runs"][0]["cases"][0]
    assert invalid["judge_status"] == "error" and "invented" in json.dumps(invalid["judge_record"])
    with pytest.raises(ValueError, match="duplicate"):
        apply_results(job, [results[0], results[0]])


@pytest.mark.parametrize("filename", ["receipt.json", "receipt.json.gz"])
def test_artifact_publish_is_atomic_and_never_overwrites(tmp_path: Path, filename: str) -> None:
    path = tmp_path / filename
    with pytest.raises(ValueError):
        save_json(path, {"invalid": float("nan")})
    assert not path.exists() and list(tmp_path.iterdir()) == []
    save_json(path, {"original": True})
    original = path.read_bytes()
    with pytest.raises(FileExistsError):
        save_json(path, {"replacement": True})
    assert path.read_bytes() == original and len(list(tmp_path.iterdir())) == 1
    save_json(path, {"replacement": True}, overwrite=True)
    replacement = path.read_bytes()
    with pytest.raises(ValueError):
        save_json(path, {"invalid": float("nan")}, overwrite=True)
    assert path.read_bytes() == replacement
    assert load_json(path) == {"replacement": True}


@pytest.mark.parametrize("filename", ["execution.json", "tools.jsonl"])
async def test_damaged_recovery_stops_only_that_case(tmp_path: Path, filename: str) -> None:
    cases = [AgentCase(cid, "fixture", cid, {"goal": "fixture"}) for cid in ["A", "B"]]
    directory = tmp_path / "run"
    (directory / "0001").mkdir(parents=True)
    artifact = directory / "0001" / filename
    artifact.write_text('{"unfinished":')
    original = artifact.read_bytes()
    adapter = FakeAdapter(cases, delay=0)
    captured = await capture_cases(
        adapter,
        tmp_path,
        cases,
        RunConfig(),
        FunctionModel(answer),
        BudgetLedger(tmp_path / "budget.json"),
        directory,
        bundle(["A", "B"]),
    )
    rows = captured["runs"][0]["cases"]
    assert adapter.prepared == 1
    assert [row["execution_status"] for row in rows] == ["unconfirmed", "completed"]
    assert rows[0]["stop_reason"] == "invalid_capture"
    assert artifact.read_bytes() == original


async def test_on_demand_skills_are_bounded_journaled_and_subject_only(tmp_path: Path) -> None:
    from dwelly_bot import prompts

    skill = tmp_path / "workflow.md"
    skill.write_text("TRUSTED_EXTRA_SKILL: verify the receipt before closing the case.")
    config = RunConfig(skills=[str(skill)], skill_mode="on_demand", domain_skill_enabled=False)
    parts = prompts.instructions("banking", config, "MANDATORY_POLICY")
    assert "domain" not in {part.name for part in parts}
    assert "TRUSTED_EXTRA_SKILL" not in str(parts) and "MANDATORY_POLICY" in str(parts)
    observed = 0

    def respond(messages: list[ModelMessage], info: AgentInfo) -> ModelResponse:
        nonlocal observed
        observed += 1
        if observed == 1:
            assert {tool.name for tool in info.function_tools} >= {"list_skills", "read_skill"}
            return ModelResponse([ToolCallPart("read_skill", {"skill_id": "skill-0", "limit": 20})])
        returns = [
            part
            for message in messages
            for part in message.parts
            if isinstance(part, ToolReturnPart)
        ]
        content = returns[-1].content
        assert isinstance(content, dict)
        assert len(content["text"]) == 20 and content["next_offset"] == 20
        assert content["trusted_workflow"] is True
        return answer(messages, info)

    journal = Journal(tmp_path / "tools.jsonl")

    runtime = CaseRuntime(FunctionModel(respond), config, journal)
    agent = runtime.agent(output_type=SolutionOutput, output_name="resolve", instructions=parts)
    await runtime.ask(agent, "fixture")
    journal.close()
    assert journal.events[0]["tool"] == "read_skill" and journal.events[0]["read_only"] is True
    assert journal.events[0]["status"] == "returned"


@pytest.mark.parametrize(
    "path", ["/rows/-1", "/rows/01", "/rows/+1", "/rows/1.0", "/rows/\u0661", "/bad~2"]
)
def test_invalid_pointers_cannot_select_a_different_observation(path: str) -> None:
    with pytest.raises(ValueError):
        pointer({"rows": ["first", "last"]}, path)


def test_json_pointer_root_escaping_and_missing_members() -> None:
    data = {"": 0, "a/b": {"~1": "observed"}, "rows": ["first", "last"]}
    assert pointer(data, "") == (True, data)
    assert pointer(data, "/") == (True, 0)
    assert pointer(data, "/a~1b/~01") == (True, "observed")
    assert pointer(data, "/rows/-") == pointer(data, "/rows/2") == (False, None)


@pytest.mark.parametrize("number", [float("nan"), float("inf"), -float("inf")])
async def test_invalid_tool_numbers_stop_without_repeating_an_effect(
    tmp_path: Path, number: float
) -> None:
    journal = Journal(tmp_path / "tools.jsonl")
    effects = 0

    def mutate() -> dict[str, Any]:
        nonlocal effects
        effects += 1
        assert (
            json.loads(Path(journal.file.name).read_text().splitlines()[-1])["status"] == "started"
        )
        return {"amount": number}

    def subject(_: Any, info: AgentInfo) -> ModelResponse:
        return ModelResponse([ToolCallPart("mutate", {})])

    runtime = CaseRuntime(FunctionModel(subject), RunConfig(retries=2), journal)

    agent = runtime.agent(
        output_type=SolutionOutput,
        output_name="finish",
        instructions="Perform one operation",
        tools=[runtime.tool("mutate", "Change state", mutate)],
    )
    with pytest.raises(ValueError, match="JSON compliant"):
        await runtime.ask(agent, "Perform the operation")
    journal.close()
    assert effects == runtime.usage.requests == 1
    assert all(event["status"] == "error" and "result" not in event for event in journal.events)


async def test_explicit_reasoning_is_forwarded_for_a_model_outside_the_snapshot(
    tmp_path: Path,
) -> None:
    observed: list[Any] = []

    def respond(_: Any, info: AgentInfo) -> ModelResponse:
        observed.append(info.model_settings)
        return ModelResponse([TextPart("Done")])

    profile = ModelProfile(model="new-model", reasoning_enabled=True)
    model = BudgetedModel(
        FunctionModel(respond), BudgetLedger(tmp_path / "ledger.json"), "A", profile=profile
    )
    await Agent(model).run("Request")
    assert observed[0]["openrouter_reasoning"] == {"enabled": True}
    assert observed[0]["openrouter_provider"]["require_parameters"] is True


@pytest.mark.parametrize("selection", [{"limit": -1}, {"ids": []}, {"ids": ["A", "A"]}])
async def test_invalid_case_selection_cannot_start_a_run(
    tmp_path: Path, selection: dict[str, Any]
) -> None:
    with pytest.raises(RunFailure, match=r"nonnegative|nonempty and unique"):
        await execute("dwelly-banking", RunConfig(), dataset_root=tmp_path, **selection)
    assert list(tmp_path.iterdir()) == []


def test_check_rejects_unknown_arguments(monkeypatch: pytest.MonkeyPatch) -> None:
    from dwelly_bot import checks

    monkeypatch.setattr(
        checks, "check", lambda: pytest.fail("An invalid command cannot start checks")
    )
    with pytest.raises(SystemExit) as error:
        main(["check", "--not-an-option"])
    assert error.value.code == 2


@pytest.mark.parametrize("concurrency", [1, 3, 10])
async def test_capture_respects_concurrency_and_keeps_case_order(
    tmp_path: Path,
    concurrency: int,
) -> None:
    active = peak = 0

    class Session(FakeSession):
        async def run(self, runtime: CaseRuntime) -> SolutionOutput:
            nonlocal active, peak
            active += 1
            peak = max(peak, active)
            try:
                return await super().run(runtime)
            finally:
                active -= 1

    class Adapter(FakeAdapter):
        def prepare(self, case: AgentCase, root: Path, config: RunConfig) -> FakeSession:
            return Session(case, delay=0.01)

    cases = [AgentCase(str(i), "fixture", str(i), {}) for i in range(23)]
    saved = await capture_cases(
        Adapter(cases),
        tmp_path,
        cases,
        RunConfig(case_concurrency=concurrency),
        FunctionModel(answer),
        BudgetLedger(tmp_path / "ledger.json"),
        tmp_path,
        bundle([c.id for c in cases]),
    )
    assert peak == concurrency and active == 0
    assert [c["answer"] for c in saved["runs"][0]["cases"]] == [c.id for c in cases]
    export(saved, tmp_path / "ANSWERS")
    assert (tmp_path / "ANSWERS/23/ANSWER.md").read_text() == "22\n"


async def test_shared_adapter_cannot_bypass_concurrency_guard(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    cases = [AgentCase("A", "fixture", "A", {})]
    adapter = FakeAdapter(cases)
    monkeypatch.setattr(adapter, "state_mode", "shared")
    with pytest.raises(ValueError, match="Shared adapter state"):
        await capture_cases(
            adapter,
            tmp_path,
            cases,
            RunConfig(case_concurrency=3),
            FunctionModel(answer),
            BudgetLedger(tmp_path / "ledger.json"),
            tmp_path / "run",
            bundle(["A"]),
        )
    assert adapter.prepared == 0 and not (tmp_path / "run").exists()


def test_run_exports_failed_answers_and_rejects_occupied_destination_before_execution(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from dwelly_bot.experiments import agent_cli

    saved = bundle(["failed", "missing"])
    saved["runs"][0]["cases"] = [{"id": "failed", "execution_status": "error", "error": "fixture"}]
    result = tmp_path / "results.json.gz"
    save_json(result, saved)
    calls = 0

    async def execute(*args: Any, **kwargs: Any) -> Path:
        nonlocal calls
        calls += 1
        assert args[1].case_concurrency == 10
        return result

    monkeypatch.setattr(agent_cli, "execute", execute)
    destination = tmp_path / "ANSWERS"
    argv = ["run", "dwelly-banking", "--concurrency", "10", "--answers", str(destination)]
    assert agent_cli.main(argv) == 1
    assert calls == 1 and (destination / "2/REASONING.md").exists()
    with pytest.raises(ValueError, match="empty directory"):
        agent_cli.main(argv)
    assert calls == 1


def test_budget_command_reads_selected_config_ledger(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    ledger = tmp_path / "spend.json"
    BudgetLedger(ledger, 36).reserve_account(2, "fixture", "case")
    config = tmp_path / "config.json"
    config.write_text(json.dumps({"budget_file": str(ledger), "total_budget_usd": 36}))
    assert main(["agent", "budget", "--config", str(config)]) == 0
    assert json.loads(capsys.readouterr().out)["exposure_usd"] == 2
