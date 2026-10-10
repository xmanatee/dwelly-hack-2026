"""Scripted offline control checkpoint and blocked disclosure, using the common runtime/UI."""

import argparse
import asyncio
import json
import os
import time
from collections.abc import Awaitable, Callable
from pathlib import Path
from typing import Any, cast

from pydantic_ai.messages import ModelResponse, ToolCallPart
from pydantic_ai.models.function import FunctionModel

from dwelly_bot.context.evidence import EvidenceText
from dwelly_bot.contracts import RunConfig
from dwelly_bot.experiments.journal import Journal
from dwelly_bot.harness.control_checks import ControlChecklist, ControlQuestion, ControlRequired
from dwelly_bot.harness.runtime import CaseRuntime
from dwelly_bot.reporting import Report, render
from dwelly_bot.reporting.resources import summarize
from dwelly_bot.storage import json_bytes, save_json


async def run(output: Path) -> None:
    os.environ["PYDANTIC_AI_NO_BANNER"] = "1"
    output.mkdir(parents=True, exist_ok=False)
    questions = [
        ControlQuestion.model_validate(q)
        for q in json.loads(Path(__file__).with_name("questions.json").read_text())
    ]
    sources = [
        EvidenceText(
            id="message",
            text="Please explain this slowly; I cannot follow the account changes.",
            source="Customer message",
            origin="message",
            speaker="customer",
        ),
        EvidenceText(
            id="ticket",
            text="Approval is pending; the CRM contact is Alex but the request is signed Sam.",
            source="CRM ticket",
            origin="document",
        ),
    ]

    def scripted(messages: Any, info: Any) -> ModelResponse:
        quotes = [sources[0].text, sources[1].text, "Approval is pending"]
        return ModelResponse(
            parts=[
                ToolCallPart(
                    info.output_tools[0].name,
                    {
                        "answers": [
                            {
                                "id": q.id,
                                "value": "yes",
                                "reason": "Disclosed in the synthetic case record",
                                "evidence": [
                                    {
                                        "source_id": "message"
                                        if q.id == "support_need"
                                        else "ticket",
                                        "quote": quote,
                                    }
                                ],
                            }
                            for q, quote in zip(questions, quotes, strict=True)
                        ]
                    },
                )
            ]
        )

    journal = Journal(output / "controls.jsonl")
    runtime = CaseRuntime(FunctionModel(scripted), RunConfig(retries=0), journal)
    gate = ControlChecklist(questions, parent=runtime.policy_gate)
    runtime.policy_gate = gate
    started = time.monotonic()
    try:
        controls = await gate.assess(runtime, sources)
        effects: list[str] = []

        def share_bank_data() -> str:
            effects.append("disclosed")
            return "disclosure receipt"

        try:
            tool = runtime.tool("share_bank_data", "Synthetic disclosure", share_bank_data)
            await cast(Callable[[], Awaitable[str]], tool.function)()
        except ControlRequired:
            blocked = True
        else:
            blocked = False
        assert blocked and not effects
        save_json(output / "controls.json", controls)
        save_json(output / "model-roles.json", runtime.role_records)
        save_json(
            output / "verification.json",
            {
                "scripted_offline_control": True,
                "paid_model_requests": 0,
                "disclosure_blocked": blocked,
                "disclosure_effects": len(effects),
            },
        )
        report = Report(
            title="Required case controls",
            subtitle="Scripted offline probe · no live classification-quality or legal-compliance claim",
        )
        report.metrics(
            {
                "Questions": len(questions),
                "Disclosure blocked": blocked,
                "Actual disclosures": len(effects),
            }
        )
        resources = summarize(
            [
                {
                    "execution_status": "completed",
                    "metrics": {
                        "latency_ms": (time.monotonic() - started) * 1000,
                        "cost_usd": 0,
                        "unconfirmed_exposure_usd": 0,
                    },
                    "usage": json.loads(json_bytes(runtime.usage)),
                }
            ]
        )
        report.metrics(
            {
                "Model": runtime.model.model_name,
                "Execution time (s)": resources["latency_mean_seconds"],
                "Processing cost (USD)": resources["cost_usd"],
                "LLM requests": resources["requests"],
            },
            title="Resources — scripted offline case",
        )
        report.receipt = {
            "execution_resources": resources,
            "model": runtime.model.model_name,
            "billing": "offline_control_not_billed",
        }
        report.table(
            "Required actions",
            [
                {
                    "Question": row["question"],
                    "Answer": row["value"],
                    "Handling": row["next_step"],
                    "Required action": row["required_action"],
                    "Policy": row["policy_source"],
                }
                for row in controls["checks"]
            ],
        )
        report.records(
            "Observed evidence", [{"id": s.id, "title": s.source, "text": s.text} for s in sources]
        )
        render(report, output / "report.html")
        print(output / "report.html")
    finally:
        journal.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True, help="New local artifact directory")
    asyncio.run(run(parser.parse_args().output))
