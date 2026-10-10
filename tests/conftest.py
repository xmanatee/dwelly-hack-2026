"""Offline application checks; no accidental model or telemetry requests."""

import socket
from collections.abc import Iterator
from pathlib import Path
from typing import NoReturn

import pytest

from dwelly_bot.experiments.journal import Journal

LOOPBACK = {"127.0.0.1", "::1"}


@pytest.fixture(autouse=True)
def no_network(monkeypatch: pytest.MonkeyPatch) -> None:
    def deny(*args: object, **kwargs: object) -> NoReturn:
        raise AssertionError("Network is disabled in offline contract tests")

    connect, connect_ex = socket.socket.connect, socket.socket.connect_ex

    # Windows asyncio builds its self-pipe from a loopback socket pair; that is not network.
    def local_connect(self: socket.socket, address: object) -> None:
        if isinstance(address, tuple) and address[0] in LOOPBACK:
            return connect(self, address)
        deny()

    def local_connect_ex(self: socket.socket, address: object) -> int:
        if isinstance(address, tuple) and address[0] in LOOPBACK:
            return connect_ex(self, address)
        deny()

    monkeypatch.setattr(socket.socket, "connect", local_connect)
    monkeypatch.setattr(socket.socket, "connect_ex", local_connect_ex)
    monkeypatch.setattr(socket, "create_connection", deny)


@pytest.fixture
def journal(tmp_path: Path) -> Iterator[Journal]:
    recorder = Journal(tmp_path / "tools.jsonl")
    try:
        yield recorder
    finally:
        recorder.close()
