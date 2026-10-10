"""Exploration preserves source identity and can be reused without model screening."""

import json
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from dwelly_bot.analysis import AnalysisContext, Report, Table
from dwelly_bot.analysis.discovery_inputs import text_records
from dwelly_bot.analysis.topics import add_topics


async def test_topic_review_preserves_sources_and_reuses_computation(tmp_path: Path) -> None:
    pytest.importorskip("sklearn")
    rows = [
        {"id": str(i), "text": text}
        for i, text in enumerate(
            [
                *[f"close bank account balance transfer request {i}" for i in range(12)],
                *[f"repair heating boiler property tenant request {i}" for i in range(12)],
                "unrecognized solar telescope observation",
            ]
        )
    ]
    records = text_records(
        Table("messages", rows), id_column="id", text="text", kind="conversation", domain=""
    )
    ctx = AnalysisContext(tmp_path, tmp_path / "first", tmp_path / "cache")
    report = Report(title="Topics")
    geometry = await add_topics(report, ctx, records)
    assert {row["id"] for row in geometry["assignments"]} == {row["id"] for row in rows}
    assert len(geometry["assignments"]) == len(rows)
    assert sum(row["count"] for row in geometry["clusters"]) + sum(
        row["cluster"] == -1 for row in geometry["assignments"]
    ) == len(rows)
    for block in report.blocks:
        if block.kind == "chart":
            details = block.data["details"]
            for trace in block.data["data"]:
                for id in trace["customdata"]:
                    assert details[id]["text"] == rows[int(id)]["text"]
    ctx.save(report)
    json.loads((ctx.output / "analysis.json").read_text())
    second = AnalysisContext(tmp_path, tmp_path / "second", tmp_path / "cache")
    repeated = await add_topics(Report(title="Renamed view"), second, records)
    assert repeated == geometry
    assert all(step["status"] == "cache_hit" for step in second.steps)
    assert second.model is None


async def test_mapping_rejects_empty_text_without_silently_dropping_it(tmp_path: Path) -> None:
    records = text_records(
        Table("messages", [{"id": "a", "text": " "}]),
        id_column="id",
        text="text",
        kind="question",
        domain="",
    )
    ctx = AnalysisContext(tmp_path, tmp_path / "run", tmp_path / "cache")
    with pytest.raises(ValueError, match="empty analysis texts"):
        await add_topics(Report(title="Empty input"), ctx, records)


async def test_reusing_embeddings_in_one_analysis_does_not_bill_twice(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from pydantic_ai.models.test import TestModel

    from dwelly_bot.analysis.semantic import EmbeddingConfig, remote_vectors
    from dwelly_bot.budget import BudgetLedger
    from dwelly_bot.models import BudgetedModel

    client = AsyncMock()
    client.__aenter__.return_value = client
    client.embeddings.create.return_value = SimpleNamespace(
        model_dump=lambda: {
            "data": [{"index": 0, "embedding": [0.5, 0.5]}],
            "usage": {"cost": 0.00001},
            "id": "embedding-test",
        }
    )
    monkeypatch.setattr("openai.AsyncOpenAI", lambda **kwargs: client)
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-only")
    ctx = AnalysisContext(
        tmp_path,
        tmp_path / "run",
        tmp_path / "cache",
        model=BudgetedModel(TestModel(), BudgetLedger(tmp_path / "budget.json"), "analysis"),
    )
    records = text_records(
        Table("messages", [{"id": "a", "text": "close account"}]),
        id_column="id",
        text="text",
        kind="question",
        domain="",
    )
    first = await remote_vectors(ctx, records, EmbeddingConfig())
    second = await remote_vectors(ctx, records, EmbeddingConfig())
    assert first == second == [[0.5, 0.5]]
    assert client.embeddings.create.await_count == 1
    assert len(json.loads((tmp_path / "budget.json").read_text())["requests"]) == 1
    receipts = [json.loads(p.read_text()) for p in (ctx.output / "embeddings").glob("*.json")]
    assert sorted(row["reused"] for row in receipts) == [False, True]
