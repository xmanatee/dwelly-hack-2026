"""Optional capabilities change available tools; actor boundaries and core guards remain."""

import json
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pytest
from pydantic_ai import InstructionPart

from dwelly_bot.budget import BudgetLedger
from dwelly_bot.contracts import RunConfig
from dwelly_bot.experiments.journal import Journal
from dwelly_bot.harness.runtime import CaseRuntime


def test_common_prompt_and_trusted_variant_addendum_are_composed(tmp_path: Path) -> None:
    journal = Journal(tmp_path / "tools.jsonl")
    runtime = CaseRuntime(None, RunConfig(instructions="VARIANT_INTAKE_RULE"), journal)
    prompt = InstructionPart.join(runtime.instructions("banking")) or ""
    assert "Resolve the supplied operational case" in prompt
    assert "VARIANT_INTAKE_RULE" in prompt
    assert "instructions" in json.loads(RunConfig().model_dump_json())
    journal.close()


def test_concurrent_roles_preserve_existing_spend(tmp_path: Path) -> None:
    ledger = BudgetLedger(tmp_path / "budget.json")
    reservation = ledger.reserve_account(0.5, "fixture", "prior-run")[0]
    ledger.settle(reservation, 0.3, "provider_reported", None)

    def start(index: int) -> None:
        BudgetLedger(ledger.path).reserve_account(0.2, "fixture", f"new-{index}")

    with ThreadPoolExecutor(max_workers=4) as workers:
        list(workers.map(start, range(4)))
    summary = BudgetLedger(ledger.path).summary()
    assert summary["request_count"] == 5
    assert summary["reported_cost_usd"] == 0.3
    assert summary["exposure_usd"] == pytest.approx(1.1)
