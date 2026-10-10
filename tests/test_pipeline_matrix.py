"""Offline retrieval → answer → saved grading → report → export; no live model calls."""

import json
from pathlib import Path
from typing import Any

import pytest
from pydantic_ai.messages import ModelMessage, ModelResponse, ToolCallPart
from pydantic_ai.models.function import AgentInfo, FunctionModel

from dwelly_bot.adapters.banking import TRACK, BankingAdapter, BankingSession
from dwelly_bot.budget import BudgetLedger
from dwelly_bot.contracts import RunConfig
from dwelly_bot.evaluation.saved import grade_bundle
from dwelly_bot.experiments.agent import capture_cases
from dwelly_bot.reporting.html import render
from dwelly_bot.reporting.submission import export


async def test_shared_pipeline(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    root = tmp_path / "dataset"
    docs = root / "documents/banking-001"
    docs.mkdir(parents=True)
    (docs / "request.md").write_text("Has my payment arrived?\n")
    (docs / "history.md").write_text(
        "## 2025-01-01 08:00:00 UTC — event 001\nPayment authorised.\n"
        "## 2025-01-01 09:00:00 UTC — event 002\nRecipient credit unconfirmed.\n"
    )
    (root / "cases.json").write_text(
        json.dumps(
            [
                {
                    "id": "banking-001",
                    "organizer_id": "001",
                    "track": TRACK,
                    "split": "development",
                    "request": "Has my payment arrived?",
                    "decision_time": "2025-01-01 09:00:00 UTC",
                    "visible_events": 2,
                    "sources": [],
                }
            ]
        )
    )
    (root / "private-outcome.md").write_text("PRIVATE_FUTURE")
    adapter = BankingAdapter()
    selected = adapter.load_cases(root)
    config = RunConfig(max_requests=4)
    calls = 0

    def script(messages: list[ModelMessage], info: AgentInfo) -> ModelResponse:
        nonlocal calls
        calls += 1
        assert "PRIVATE_FUTURE" not in repr(messages)
        if calls == 1:
            return ModelResponse([ToolCallPart("read_document", {"document": "history.md"})])
        assert "Recipient credit unconfirmed" in repr(messages)
        return ModelResponse(
            [
                ToolCallPart(
                    info.output_tools[0].name,
                    {
                        "answer": "Credit is unconfirmed; a bank operator must obtain the recipient-bank record.",
                        "public_rationale": "history.md:L2 records authorisation; history.md:L4 has no confirmation of credit.",
                        "agent_disposition": "needs_info",
                    },
                )
            ]
        )

    bundle: dict[str, Any] = {
        "schema_version": 1,
        "title": "Offline contract probe",
        "runs": [
            {
                "id": "fixture",
                "cases": [],
                "manifest": {"assigned_case_ids": ["banking-001"], "state_mode": "static"},
            }
        ],
    }
    directory = tmp_path / "run"
    directory.mkdir()
    captured = await capture_cases(
        adapter,
        root,
        selected,
        config,
        FunctionModel(script),
        BudgetLedger(tmp_path / "budget.json"),
        directory,
        bundle,
    )
    row = captured["runs"][0]["cases"][0]
    assert row["execution_status"] == "completed", row.get("error")
    assert row["tool_events"][0]["read_only"] is True

    async def forbidden(*args: Any, **kwargs: Any) -> Any:
        pytest.fail("Saved grading must not run the agent")

    monkeypatch.setattr(BankingSession, "run", forbidden)
    graded, _ = await grade_bundle(captured, root, adapter, config)
    verifier = graded["runs"][0]["cases"][0]["verifier"]
    assert verifier["goal_pass"] is None
    assert verifier["checks"][2]["status"] == "pass"
    render(graded, directory / "report.html")
    export(graded, directory / "export")
    assert (directory / "export/1/ANSWER.md").read_text().strip() == row["answer"]
    assert "banking-001" in (directory / "export/1/REASONING.md").read_text()
    assert "PRIVATE_FUTURE" not in (directory / "report.html").read_text()
