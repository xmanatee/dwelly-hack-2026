"""Loopback-only live status; no input, model transcript or credentials are served."""

from __future__ import annotations

import argparse
from contextlib import suppress
from datetime import UTC, datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any

from dwelly_bot.experiments.bundle import verified_outcome
from dwelly_bot.reporting.page import document
from dwelly_bot.storage import save_json


def progress(
    directory: Path, run: dict[str, Any], active: set[str], budget: dict[str, Any]
) -> None:
    value = {
        "run": run["id"],
        "updated_at": datetime.now(UTC).isoformat(),
        "assigned": len(run["manifest"]["assigned_case_ids"]),
        "active": sorted(active),
        "cases": [
            {
                "id": c["id"],
                "status": c["execution_status"],
                "disposition": c.get("agent_disposition"),
                "verified_goal": verified_outcome(c),
            }
            for c in run["cases"]
        ],
        "budget": {k: v for k, v in budget.items() if k != "accounts"},
    }
    save_json(directory / "status.json", value, overwrite=True)


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(prog="dwelly-bot monitor")
    parser.add_argument("directory", type=Path)
    parser.add_argument("--port", type=int, default=8765)
    args = parser.parse_args(argv)
    status = args.directory.resolve() / "status.json"
    page = document("monitor", "dwelly-bot live").encode()

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self) -> None:
            if self.path == "/":
                data, content_type = page, "text/html; charset=utf-8"
            elif self.path == "/status.json" and status.is_file():
                data, content_type = status.read_bytes(), "application/json"
            else:
                self.send_error(404)
                return
            self.send_response(200)
            self.send_header("Content-Type", content_type)
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.end_headers()
            self.wfile.write(data)

        def log_message(self, format: str, *args: Any) -> None:
            pass

    with ThreadingHTTPServer(("127.0.0.1", args.port), Handler) as server:
        print(f"http://127.0.0.1:{args.port}", flush=True)
        with suppress(KeyboardInterrupt):
            server.serve_forever()
    return 0
