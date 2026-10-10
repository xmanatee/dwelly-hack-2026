"""Instruction composition and package resource boundaries."""

from pathlib import Path

import pytest
from pydantic_ai import InstructionPart

from dwelly_bot import prompts
from dwelly_bot.contracts import RunConfig
from dwelly_bot.resources import text


def test_instruction_parts_have_distinct_origins_and_dynamic_policy() -> None:
    parts = prompts.instructions("banking", RunConfig(), "ROOT_POLICY")
    assert [part.name for part in parts] == ["common", "domain", "policy-0"]
    assert [part.dynamic for part in parts] == [False, False, True]
    assert InstructionPart.join(parts)


def test_package_resources_are_independent_from_working_directory(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    assert "Resolve the supplied operational case" in text("prompts/case-agent.md")
    with pytest.raises(ValueError, match="inside the package"):
        text("../.env")
