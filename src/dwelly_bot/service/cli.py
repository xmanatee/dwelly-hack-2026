"""Provision trusted local sessions or serve authenticated text turns."""

import argparse
import json
from collections.abc import Sequence
from pathlib import Path

from dwelly_bot.channels.intake import inbound_adapter
from dwelly_bot.context.collector import ContextSource
from dwelly_bot.context.sources import JsonSource
from dwelly_bot.service.store import SessionStore


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--state", type=Path, default=Path(".cache/service/sessions.sqlite"))
    sub = parser.add_subparsers(dest="command", required=True)
    create = sub.add_parser(
        "bind", help="Create a session from trusted local email/call/ticket JSON"
    )
    create.add_argument("--input", type=Path, required=True)
    create.add_argument("--ttl", type=int, default=3600)
    serve = sub.add_parser("serve")
    serve.add_argument("--host", default="127.0.0.1")
    serve.add_argument("--port", type=int, default=8780)
    serve.add_argument("--records", type=Path)
    serve.add_argument("--dataset", type=Path)
    serve.add_argument("--planner-config", type=Path)
    serve.add_argument("--context-config", type=Path)
    serve.add_argument("--output", type=Path, default=Path(".cache/service/captures"))
    serve.add_argument("--timeout", type=float, default=45)
    args = parser.parse_args(argv)
    try:
        inputs = [
            getattr(args, key, None)
            for key in ("input", "records", "planner_config", "context_config")
        ]
        if any(p and p.resolve() == args.state.resolve() for p in inputs):
            raise ValueError("Session state must not overwrite an input/config file")
        if args.command == "bind":
            event = inbound_adapter.validate_json(args.input.read_text())
            session, token = SessionStore(args.state).create(event, args.ttl)
            print(json.dumps({"session_id": session, "token": token, "expires_in": args.ttl}))
            return 0
        import uvicorn

        from dwelly_bot.service.app import create_app
        from dwelly_bot.service.backend import PipelineBackend

        if args.state.resolve().is_relative_to(args.output.resolve()):
            raise ValueError("Session state must be outside capture output")
        sources: list[ContextSource] = []
        manifest = None
        if args.dataset:
            from dwelly_bot.adapters.synthetic_banking.sources import bank_sources
            from dwelly_bot.local_cli import dataset_manifest

            if any(
                p.resolve().is_relative_to(args.dataset.resolve())
                for p in (args.state, args.output)
            ):
                raise ValueError("State and captures must be outside the dataset")
            manifest = dataset_manifest(args.dataset)
            sources.extend(bank_sources(args.dataset))
        if args.records:
            sources.append(JsonSource(args.records))
        store = SessionStore(args.state)
        backend = PipelineBackend(
            store,
            tuple(sources),
            args.output,
            planner_config=args.planner_config,
            context_config=args.context_config,
            dataset=manifest,
        )
        uvicorn.run(
            create_app(store, backend, timeout=args.timeout),
            host=args.host,
            port=args.port,
            access_log=False,
        )
        return 0
    except (OSError, ValueError) as exc:
        parser.exit(2, f"Service failed: {exc}\n")
    except ImportError:
        parser.exit(2, "Install the optional service: uv sync --extra server\n")
