"""Claude Code subscription transport: structured output, usage and failures without a real CLI."""

import json
import sys
from pathlib import Path

import pytest
from pydantic import BaseModel
from pydantic_ai import Agent

from dwelly_bot.analysis.claude_code import claude_code_model


class Topic(BaseModel):
    topic: str


def fake_cli(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, reply: dict[str, object]) -> Path:
    log = tmp_path / "argv.json"
    script = tmp_path / "claude"
    script.write_text(
        f"#!{sys.executable}\nimport json, sys\n"
        f"json.dump({{'argv': sys.argv[1:], 'stdin': sys.stdin.read()}}, open({str(log)!r}, 'w'))\n"
        f"print({json.dumps(json.dumps(reply))})\n"
    )
    script.chmod(0o755)
    monkeypatch.setenv("PATH", str(tmp_path))
    return log


async def test_structured_output_and_api_equivalent_cost(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    log = fake_cli(
        tmp_path,
        monkeypatch,
        {
            "structured_output": {"topic": "Lost card"},
            "total_cost_usd": 0.01,
            "session_id": "s",
            "usage": {"input_tokens": 2, "cache_creation_input_tokens": 8, "output_tokens": 5},
        },
    )
    agent = Agent(claude_code_model("claude-code/haiku"), output_type=Topic, instructions="Label")
    result = await agent.run("I lost my card")
    assert result.output.topic == "Lost card"
    response = result.all_messages()[-2]
    assert getattr(response, "provider_details", {})["cost"] == 0.01
    assert result.usage.input_tokens == 10
    call = json.loads(log.read_text())
    assert call["argv"][call["argv"].index("--model") + 1] == "haiku"
    assert "--tools=" in call["argv"] and call["stdin"] == "I lost my card"


async def test_cli_error_is_not_an_output(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    fake_cli(tmp_path, monkeypatch, {"is_error": True, "subtype": "error", "result": "limit"})
    agent = Agent(claude_code_model("claude-code/sonnet"), output_type=Topic)
    with pytest.raises(RuntimeError, match="limit"):
        await agent.run("x")


async def test_one_retry_after_cli_schema_exhaustion(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    counter = tmp_path / "calls"
    script = tmp_path / "claude"
    script.write_text(
        f"#!{sys.executable}\nimport json, pathlib, sys\nsys.stdin.read()\n"
        f"p = pathlib.Path({str(counter)!r})\nn = int(p.read_text()) if p.exists() else 0\n"
        "p.write_text(str(n + 1))\n"
        "print(json.dumps({'is_error': True, 'subtype': 'error_max_structured_output_retries'}"
        " if n == 0 else {'structured_output': {'topic': 'ok'}}))\n"
    )
    script.chmod(0o755)
    monkeypatch.setenv("PATH", str(tmp_path))
    agent = Agent(claude_code_model("claude-code/haiku"), output_type=Topic)
    assert (await agent.run("x")).output.topic == "ok"
    assert counter.read_text() == "2"
