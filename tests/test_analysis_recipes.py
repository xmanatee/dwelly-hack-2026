"""Visible-only analysis and explicit public retrospective review stay separate."""

from pathlib import Path

import pytest

from dwelly_bot.analysis import AnalysisContext, banking, banking_review
from dwelly_bot.paths import DATASET


async def test_actual_public_recipe(tmp_path: Path) -> None:
    pytest.importorskip("plotly")
    if not (DATASET / "cases.json").is_file():
        pytest.skip("Optional local dataset not installed")
    ctx = AnalysisContext(DATASET, tmp_path / "run", tmp_path / "cache", parameters={"sample": 5})
    report = await banking.build(ctx)
    assert report.blocks[0].data["Cases"] == 50
    assert any(block.kind == "chart" for block in report.blocks)
    assert any(block.kind == "records" for block in report.blocks)
    assert all("original" not in source and "release.zip" not in source for source in ctx.sources)
    assert ctx.model is None
    assert ctx.save(report).is_file()


async def test_explicit_retrospective_recipe_reads_public_later_evidence(tmp_path: Path) -> None:
    if not (DATASET / "cases.json").is_file():
        pytest.skip("Optional local dataset not installed")
    ctx = AnalysisContext(DATASET, tmp_path / "review", tmp_path / "cache")
    report = await banking_review.build(ctx)
    assert report.blocks[0].data["Cases"] == 50
    assert report.blocks[0].data["History events"] == 258
    assert report.blocks[0].data["Original attachments"] == 9
    assert "future events" in report.subtitle
    assert any("original" in source for source in ctx.sources)
    records = next(block.data["rows"] for block in report.blocks if block.kind == "records")
    assert len(records) == 50
    assert "event 005" in records[0]["sources"][1]["text"]
    assert ctx.model is None
