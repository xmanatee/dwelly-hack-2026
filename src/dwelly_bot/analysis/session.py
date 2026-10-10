"""Local analysis execution, resumable read-only stages and optional budgeted LLM work."""

from __future__ import annotations

import json
import os
from collections.abc import Callable, Sequence
from datetime import UTC, datetime
from importlib.metadata import version
from pathlib import Path
from typing import Any

from pydantic import BaseModel
from pydantic_ai import Agent, ModelMessagesTypeAdapter, capture_run_messages
from pydantic_ai.exceptions import ModelRetry
from pydantic_ai.settings import ModelSettings
from pydantic_ai.usage import UsageLimits

from dwelly_bot.cache import JsonCache
from dwelly_bot.contracts import JsonRecord
from dwelly_bot.models import BudgetedModel
from dwelly_bot.reporting.models import Report
from dwelly_bot.storage import file_hash, fingerprint, load_json, save_json


def validate_analysis(report: Report) -> Report:
    """Saved analysis belongs to one source dataset, never a combined report bundle."""
    data = report.receipt.get("data")
    if (
        report.receipt.get("analysis_only") is not True
        or not isinstance(data, str)
        or not data.strip()
    ):
        raise ValueError("An analysis report requires exactly one dataset in its receipt")
    if report.receipt.get("source_analyses"):
        raise ValueError("Combined analysis reports are unsupported; select one dataset analysis")
    return report


class AnalysisContext:
    def __init__(
        self,
        data: Path,
        output: Path,
        cache: Path,
        *,
        parameters: JsonRecord | None = None,
        code_hash: str = "",
        model: BudgetedModel | None = None,
        model_settings: ModelSettings | None = None,
    ) -> None:
        self.data = data.resolve()
        self.output = output.resolve()
        self.output.mkdir(parents=True, exist_ok=False)
        self.cache = JsonCache(cache)
        self.parameters = parameters or {}
        core = Path(__file__).parent
        self.code_hash = code_hash or fingerprint({p.name: file_hash(p) for p in core.glob("*.py")})
        # Changing a chart or recipe layout must not repeat a paid extraction.
        self.llm_code_hash = fingerprint(
            {
                "files": {
                    str(p): file_hash(p)
                    for p in [
                        core / "llm.py",
                        core / "session.py",
                        core.parent / "context/evidence.py",
                        core.parent / "models.py",
                    ]
                },
                "dependencies": {name: version(name) for name in ["pydantic", "pydantic-ai-slim"]},
            }
        )
        self.model = model
        self.model_settings = model_settings or {"max_tokens": 2048}
        self.sources: dict[str, str] = {}
        self.steps: list[JsonRecord] = []
        self.last_model_trace: JsonRecord | None = None

    def event(self, event: JsonRecord) -> None:
        with (self.output / "events.jsonl").open("a") as output:
            output.write(
                json.dumps({"at": datetime.now(UTC).isoformat(), **event}, allow_nan=False) + "\n"
            )
            output.flush()
            os.fsync(output.fileno())

    def cached(
        self,
        name: str,
        inputs: Any,
        compute: Callable[[], Any],
        *,
        files: Sequence[Path] = (),
    ) -> Any:
        hashes: dict[str, str] = {}
        for path in files:
            source = path.resolve()
            if not source.is_relative_to(self.data):
                raise ValueError("Dataset loader source must remain inside its data directory")
            hashes[str(source.relative_to(self.data))] = file_hash(source)
        self.sources.update(hashes)
        key = fingerprint(
            {"stage": name, "inputs": inputs, "sources": hashes, "code": self.code_hash}
        )
        self.event({"stage": name, "key": key, "status": "started"})
        try:
            result, hit = self.cache.compute(key, compute)
        except BaseException as error:
            self.event({"stage": name, "key": key, "status": "error", "error": str(error)})
            raise
        step = {"stage": name, "key": key, "status": "cache_hit" if hit else "computed"}
        self.steps.append(step)
        self.event(step)
        return result

    async def ask[T: BaseModel](
        self,
        name: str,
        inputs: JsonRecord,
        output_type: type[T],
        instructions: str,
        *,
        validate: Callable[[T], None] | None = None,
        repair: bool = False,
    ) -> T:
        if self.model is None:
            raise RuntimeError("This stage requires an explicitly supplied budgeted model")
        key = fingerprint(
            {
                "stage": name,
                "input": inputs,
                "schema": output_type.model_json_schema(),
                "instructions": instructions,
                "model": self.model.model_name,
                "supports_reasoning": self.model.supports_reasoning,
                "billing_profile": self.model.billing_profile.model_dump(
                    exclude={"key_envs", "account_budget_usd"}
                ),
                "settings": self.model_settings,
                "code": self.llm_code_hash,
            }
        )
        async with self.cache.async_locked(key):
            cached = self.cache.get(key)
            if cached is not None:
                result = output_type.model_validate(cached["output"])
                if validate:
                    validate(result)
                step = {"stage": name, "key": key, "status": "cache_hit", "new_requests": 0}
                self.steps.append(step)
                self.event(step)
                self.last_model_trace = {
                    **cached,
                    "reused": True,
                    "new_requests": 0,
                    "cache_key": key,
                }
                save_json(
                    self.output / "steps" / f"{len(self.steps):04d}-{key[:12]}.json",
                    self.last_model_trace,
                )
                return result
            self.event({"stage": name, "key": key, "status": "started", "input": inputs})
            request_model = self.model.scoped(self.model.case_id + "/" + key[:12])
            agent: Agent[None, T] = Agent(
                request_model,
                output_type=output_type,
                instructions=instructions,
                retries=1 if repair else 0,
            )
            agent.instrument = False
            value: JsonRecord = {
                "input": inputs,
                "schema": output_type.model_json_schema(),
                "instructions": instructions,
            }
            if repair and validate:

                @agent.output_validator
                def grounded(output: T) -> T:
                    try:
                        validate(output)
                    except ValueError as error:
                        value.setdefault("invalid_outputs", []).append(
                            output.model_dump(mode="json")
                        )
                        raise ModelRetry(str(error)) from error
                    return output

            with capture_run_messages() as messages:
                try:
                    result_run = await agent.run(
                        json.dumps(inputs, ensure_ascii=False),
                        model_settings=self.model_settings,
                        usage_limits=UsageLimits(request_limit=2, total_tokens_limit=60000),
                    )
                    result = result_run.output
                    value["output"] = result.model_dump(mode="json")
                    if validate:
                        validate(result)
                    value["status"] = "completed"
                except BaseException as error:
                    value.update(status="error", error=f"{type(error).__name__}: {error}")
                    raise
                finally:
                    value["messages"] = json.loads(ModelMessagesTypeAdapter.dump_json(messages))
                    self.model.calls.extend(request_model.calls)
                    value["costs"] = request_model.calls
                    value["new_requests"] = len(request_model.calls)
                    self.last_model_trace = value
                    save_json(
                        self.output / "steps" / f"{len(self.steps) + 1:04d}-{key[:12]}.json", value
                    )
                    step = {
                        "stage": name,
                        "key": key,
                        "status": value["status"],
                        "new_requests": len(request_model.calls),
                    }
                    self.steps.append(step)
                    self.event(step)
            self.cache.put(key, value)
            return result

    def saved_run(self) -> JsonRecord:
        """Only one run on this exact corpus may contribute to source analysis."""
        from dwelly_bot.experiments.bundle import validate
        from dwelly_bot.experiments.provenance import dataset_hash

        path = Path(self.parameters["saved_run"])
        bundle = validate(load_json(path))
        if len(bundle["runs"]) != 1:
            raise ValueError("Analysis accepts one saved run from its own dataset")
        if bundle["runs"][0]["manifest"].get("dataset_hash") != dataset_hash(self.data):
            raise ValueError("Analysis and saved run must use the same pinned dataset")
        return bundle

    def receipt(self) -> JsonRecord:
        return {
            "data": str(self.data),
            "code_hash": self.code_hash,
            "parameters": self.parameters,
            "sources": self.sources,
            "steps": self.steps,
            "model": {
                "id": self.model.model_name,
                "provider_only": self.model.billing_profile.provider_only,
                "reasoning": self.model.billing_profile.reasoning_enabled,
                "settings": self.model_settings,
                "extractor_hash": self.llm_code_hash,
            }
            if self.model
            else None,
            "budget": self.model.ledger.summary() if self.model else None,
            "analysis_only": True,
        }

    def save(self, report: Report) -> Path:
        from dwelly_bot.reporting import render

        report.receipt = self.receipt()
        validate_analysis(report)
        save_json(self.output / "analysis.json", report.model_dump(mode="json"))
        destination = self.output / "analysis.html"
        render(report, destination)
        return destination
