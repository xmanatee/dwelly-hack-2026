"""Offline application checks; no accidental model or telemetry requests."""

import socket
from collections.abc import Iterator
from pathlib import Path
from typing import NoReturn

import pytest

from dwelly_bot.experiments.journal import Journal


@pytest.fixture(autouse=True)
def no_network(monkeypatch: pytest.MonkeyPatch) -> None:
    def deny(*args: object, **kwargs: object) -> NoReturn:
        raise AssertionError("Network is disabled in offline contract tests")

    monkeypatch.setattr(socket.socket, "connect", deny)
    monkeypatch.setattr(socket.socket, "connect_ex", deny)
    monkeypatch.setattr(socket, "create_connection", deny)


@pytest.fixture
def journal(tmp_path: Path) -> Iterator[Journal]:
    recorder = Journal(tmp_path / "tools.jsonl")
    try:
        yield recorder
    finally:
        recorder.close()
