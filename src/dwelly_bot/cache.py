"""Content-addressed JSON cache for read-only transforms; never cache business actions."""

from __future__ import annotations

import asyncio
import fcntl
from collections.abc import AsyncIterator, Callable, Iterator
from contextlib import asynccontextmanager, contextmanager
from pathlib import Path
from typing import Any

from dwelly_bot.storage import fingerprint, load_json, save_json


class JsonCache:
    def __init__(self, directory: Path) -> None:
        self.directory = directory
        directory.mkdir(parents=True, exist_ok=True)

    def _path(self, key: str, suffix: str) -> Path:
        if len(key) != 64 or any(c not in "0123456789abcdef" for c in key):
            raise ValueError("Cache keys must be SHA-256 digests")
        return self.directory / (key + suffix)

    @contextmanager
    def locked(self, key: str) -> Iterator[None]:
        with self._path(key, ".lock").open("a+") as lock:
            fcntl.flock(lock.fileno(), fcntl.LOCK_EX)
            yield

    @asynccontextmanager
    async def async_locked(self, key: str) -> AsyncIterator[None]:
        with self._path(key, ".lock").open("a+") as lock:
            async with asyncio.timeout(180):
                while True:
                    try:
                        fcntl.flock(lock.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                        break
                    except BlockingIOError:
                        await asyncio.sleep(0.1)
            yield

    def get(self, key: str) -> Any | None:
        path = self._path(key, ".json.gz")
        if not path.exists():
            return None
        # Corruption is an error, not permission to repeat a potentially paid call.
        envelope = load_json(path)
        if (
            envelope["value"] is None
            or envelope["key"] != key
            or fingerprint(envelope["value"]) != envelope["digest"]
        ):
            raise ValueError("Cache content does not match its receipt")
        return envelope["value"]

    def put(self, key: str, value: Any) -> None:
        if value is None:
            raise ValueError("A cached transform must return a JSON value")
        save_json(
            self._path(key, ".json.gz"),
            {"key": key, "digest": fingerprint(value), "value": value},
            overwrite=True,
        )

    def compute(self, key: str, function: Callable[[], Any]) -> tuple[Any, bool]:
        with self.locked(key):
            cached = self.get(key)
            if cached is not None:
                return cached, True
            result = function()
            self.put(key, result)
            return result, False
