"""Actual Anthropic SDK request/result mapping over an offline transport."""

import json
from pathlib import Path
from typing import Any

import httpx2 as httpx
import pytest

from dwelly_bot.budget import BudgetLedger
from dwelly_bot.evaluation.batch import collect, prepare, recover, submit
from dwelly_bot.evaluation.judge import ROOT


@pytest.mark.parametrize("lost_response_at", [None, 1, 2])
@pytest.mark.parametrize("resume_from_raw", [False, True])
def test_batch_sdk_lifecycle_preserves_results_and_accounts(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    lost_response_at: int | None,
    resume_from_raw: bool,
) -> None:
    import anthropic

    native_client = anthropic.Anthropic
    batches: dict[str, list[dict[str, Any]]] = {}
    attempts = 0
    rubric = json.loads((ROOT / "rubrics/default.json").read_text())
    config = tmp_path / "config.json"
    config.write_text(
        json.dumps(
            {
                "provider": "anthropic",
                "model": "fixture",
                "input_price_per_million": 2,
                "output_price_per_million": 8,
                "key_envs": ["BATCH_FIXTURE_A", "BATCH_FIXTURE_B"],
                "budget_file": str(tmp_path / "budget.json"),
            }
        )
    )
    monkeypatch.setenv("BATCH_FIXTURE_A", "offline-a")
    monkeypatch.setenv("BATCH_FIXTURE_B", "offline-b")

    def batch_json(bid: str, ended: bool) -> dict[str, Any]:
        count = len(batches[bid])
        return {
            "id": bid,
            "type": "message_batch",
            "processing_status": "ended" if ended else "in_progress",
            "request_counts": {
                "processing": 0 if ended else count,
                "succeeded": count if ended else 0,
                "errored": 0,
                "canceled": 0,
                "expired": 0,
            },
            "ended_at": "2026-10-09T01:00:00Z" if ended else None,
            "created_at": "2026-10-09T00:00:00Z",
            "expires_at": "2026-10-10T00:00:00Z",
            "archived_at": None,
            "cancel_initiated_at": None,
            "results_url": f"https://api.anthropic.com/v1/messages/batches/{bid}/results"
            if ended
            else None,
        }

    def respond(request: httpx.Request) -> httpx.Response:
        nonlocal attempts
        if request.method == "POST":
            attempts += 1
            bid = "msgbatch_fixture_" + str(attempts)
            batches[bid] = json.loads(request.content)["requests"]
            assert all(r["params"]["tool_choice"]["name"] == "submit_review" for r in batches[bid])
            if attempts == lost_response_at:
                raise httpx.ReadError(
                    "Lost response after provider accepted batch", request=request
                )
            return httpx.Response(200, json=batch_json(bid, False))
        bid = (
            request.url.path.split("/")[-2]
            if request.url.path.endswith("/results")
            else request.url.path.split("/")[-1]
        )
        if request.url.path.endswith("/results"):
            rows = []
            for item in batches[bid]:
                review = {
                    "summary": "Offline transport fixture",
                    "findings": [
                        {
                            "criterion": c["id"],
                            "status": "unknown",
                            "reason": "Fixture lacks independent result evidence",
                            "evidence_ids": ["TASK"],
                        }
                        for c in rubric["criteria"]
                    ],
                }
                rows.append(
                    {
                        "custom_id": item["custom_id"],
                        "result": {
                            "type": "succeeded",
                            "message": {
                                "id": "msg_fixture",
                                "type": "message",
                                "role": "assistant",
                                "model": "fixture",
                                "stop_reason": "tool_use",
                                "stop_sequence": None,
                                "content": [
                                    {
                                        "type": "tool_use",
                                        "id": "tool_fixture",
                                        "name": "submit_review",
                                        "input": review,
                                    }
                                ],
                                "usage": {
                                    "input_tokens": 10,
                                    "output_tokens": 10,
                                    "cache_read_input_tokens": 0,
                                    "cache_creation_input_tokens": 0,
                                },
                            },
                        },
                    }
                )
            return httpx.Response(
                200,
                content="\n".join(json.dumps(row) for row in rows) + "\n",
                headers={"content-type": "application/jsonl"},
            )
        return httpx.Response(200, json=batch_json(bid, True))

    def client(**kwargs: Any) -> Any:
        return native_client(
            **kwargs, http_client=httpx.Client(transport=httpx.MockTransport(respond))
        )

    monkeypatch.setattr("dwelly_bot.evaluation.batch.Anthropic", client)
    saved = {
        "schema_version": 1,
        "runs": [
            {
                "id": "fixture",
                "manifest": {"assigned_case_ids": ["A", "B"]},
                "cases": [
                    {
                        "id": cid,
                        "input": {"request": "fixture"},
                        "execution_status": "completed",
                        "verifier": {"goal_pass": False},
                    }
                    for cid in ["A", "B"]
                ],
            }
        ],
    }
    directory = tmp_path / "job"
    prepare(saved, config, directory, rubric)
    if lost_response_at:
        with pytest.raises(RuntimeError, match="uncertain"):
            submit(directory)
        # A hard process crash may leave only write-ahead reservations, without an exception log.
        for path in directory.glob("uncertain-*.json"):
            path.unlink()
        recover(
            directory,
            "msgbatch_fixture_" + str(lost_response_at),
            "BATCH_FIXTURE_A" if lost_response_at == 1 else "BATCH_FIXTURE_B",
        )
        if lost_response_at == 1:
            with pytest.raises(ValueError, match="unconfirmed"):
                recover(directory, "msgbatch_fixture_1", "BATCH_FIXTURE_B")
    else:
        submit(directory)
    expected_batches = lost_response_at or 2
    assert attempts == expected_batches
    assert (
        BudgetLedger(tmp_path / "budget.json").summary()["uncertain_requests"] == expected_batches
    )
    with pytest.raises(ValueError, match="already attempted"):
        submit(directory)
    assert collect(directory, status_only=False) == int(expected_batches < 2)
    output = json.loads((directory / "judged.json").read_text())
    cases = output["runs"][0]["cases"]
    assert sum(c["judge_status"] == "available" for c in cases) == expected_batches
    assert all(c["verifier"]["goal_pass"] is False for c in cases)
    assert BudgetLedger(tmp_path / "budget.json").summary()["exposure_usd"] == pytest.approx(
        expected_batches * 0.00005
    )
    monkeypatch.delenv("BATCH_FIXTURE_A")
    monkeypatch.delenv("BATCH_FIXTURE_B")
    if resume_from_raw:
        (directory / "judged.json").unlink()
    (directory / "report.html").unlink()
    assert collect(directory, status_only=False) == int(expected_batches < 2)
    assert json.loads((directory / "judged.json").read_text()) == output
    assert (directory / "report.html").exists()
    assert attempts == expected_batches
    assert "offline-a" not in (directory / "job.json").read_text()
