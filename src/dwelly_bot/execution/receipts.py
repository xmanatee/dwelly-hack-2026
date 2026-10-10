"""Optional durable receipts for mock operations, serialized across local processes."""

import sqlite3
from collections.abc import Callable
from contextlib import closing
from pathlib import Path

from dwelly_bot.execution.contracts import ActionReceipt


class ReceiptStore:
    def __init__(self, path: Path | None = None) -> None:
        self.path = path
        self.memory: dict[str, tuple[str, ActionReceipt]] = {}
        if path is not None:
            path.parent.mkdir(parents=True, exist_ok=True)
            with closing(sqlite3.connect(path)) as db, db:
                db.execute(
                    "CREATE TABLE IF NOT EXISTS mock_receipts (key TEXT PRIMARY KEY, digest TEXT NOT NULL, receipt TEXT NOT NULL)"
                )

    @staticmethod
    def replay(digest: str, previous: tuple[str, ActionReceipt]) -> ActionReceipt:
        old_digest, receipt = previous
        if digest != old_digest:
            raise ValueError("Idempotency conflict: event/action ID reused with changed input.")
        return receipt.model_copy(update={"replayed": True})

    def apply(self, key: str, digest: str, invoke: Callable[[], ActionReceipt]) -> ActionReceipt:
        if self.path is None:
            if key in self.memory:
                return self.replay(digest, self.memory[key])
            receipt = invoke()
            self.memory[key] = (digest, receipt)
            return receipt
        with closing(sqlite3.connect(self.path, timeout=10)) as db, db:
            db.execute("BEGIN IMMEDIATE")
            row = db.execute(
                "SELECT digest, receipt FROM mock_receipts WHERE key = ?", (key,)
            ).fetchone()
            if row is not None:
                return self.replay(digest, (row[0], ActionReceipt.model_validate_json(row[1])))
            receipt = invoke()
            db.execute(
                "INSERT INTO mock_receipts VALUES (?, ?, ?)",
                (key, digest, receipt.model_dump_json()),
            )
            return receipt
