"""Analysis consumes visible case evidence only."""

from pathlib import Path

import pytest

from dwelly_bot.analysis import AnalysisContext, banking
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
