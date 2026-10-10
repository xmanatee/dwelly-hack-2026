"""Explicit Anthropic batch judging: prepare -> submit -> status -> collect."""

from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path
from typing import Any

from anthropic import Anthropic

from dwelly_bot.budget import BudgetLedger
from dwelly_bot.configuration import read_config
from dwelly_bot.contracts import RunConfig
from dwelly_bot.evaluation.judge import (
    ROOT,
    InvalidReview,
    JudgeResult,
    evidence_pack,
    review_fields,
    validated_review,
)
from dwelly_bot.evaluation.runner import evaluation_status
from dwelly_bot.experiments.bundle import validate
from dwelly_bot.providers import credentials, ledger_path, profile_for
from dwelly_bot.reporting.html import render
from dwelly_bot.resources import text
from dwelly_bot.storage import fingerprint, load_json, save_json


def prepare(
    bundle: dict[str, Any], config_path: Path, directory: Path, rubric: dict[str, Any]
) -> None:
    config = read_config(config_path)
    if config.provider != "anthropic":
        raise ValueError("Batch judging requires direct Anthropic")
    if config.reasoning_effort:
        raise ValueError(
            "Batch judge uses a forced structured tool; thinking/effort is unsupported"
        )
    bundle = validate(copy.deepcopy(bundle))
    directory.mkdir(parents=True, exist_ok=False)
    items = []
    for run in bundle["runs"]:
        for case in run["cases"]:
            payload = evidence_pack(case, rubric)
            custom_id = fingerprint([run["id"], case["id"]])[:40]
            params = {
                "model": config.model,
                "max_tokens": config.max_tokens,
                "system": text("prompts/judge.md"),
                "messages": [{"role": "user", "content": json.dumps(payload, ensure_ascii=False)}],
                "tools": [
                    {
                        "name": "submit_review",
                        "description": "Return one cited verdict per rubric criterion",
                        "input_schema": JudgeResult.model_json_schema(),
                    }
                ],
                "tool_choice": {"type": "tool", "name": "submit_review"},
            }
            items.append(
                {
                    "custom_id": custom_id,
                    "run_id": run["id"],
                    "case_id": case["id"],
                    "payload": payload,
                    "params": params,
                }
            )
    save_json(
        directory / "job.json",
        {
            "config": config.model_dump(),
            "ledger": str(ledger_path(config)),
            "rubric": rubric,
            "bundle": bundle,
            "items": items,
            "profile_hash": fingerprint(
                {
                    "config": config.model_dump(),
                    "rubric": rubric,
                    "instructions": text("prompts/judge.md"),
                    "code": Path(__file__).read_text(),
                    "judge_code": (ROOT / "judge.py").read_text(),
                }
            ),
        },
    )


def submit(directory: Path) -> None:
    if (directory / "reservations.json").exists():
        raise ValueError(
            "Submission was already attempted; recover its provider batch ID instead of resubmitting"
        )
    job = load_json(directory / "job.json")
    config = RunConfig.model_validate(job["config"])
    keys = credentials(profile_for(config))
    ledger = BudgetLedger(Path(job["ledger"]), config.total_budget_usd)
    reservations = []
    try:
        for item in job["items"]:
            size = len(json.dumps(item["params"]).encode()) + 4096
            upper = (
                size * float(config.input_price_per_million or 0)
                + config.max_tokens * float(config.output_price_per_million or 0)
            ) / 2_000_000
            token, account = ledger.reserve_account(
                upper,
                config.model,
                "batch/" + item["custom_id"],
                {"anthropic:" + n: config.account_budget_usd for n in keys},
            )
            reservations.append(
                {"custom_id": item["custom_id"], "token": token, "account": account}
            )
    except Exception:
        # These reservations have not reached the provider yet.
        for reservation in reservations:
            ledger.settle(reservation["token"], 0, "not_submitted", None)
        raise
    save_json(directory / "reservations.json", reservations)
    receipts: list[dict[str, Any]] = []
    for account in sorted({r["account"] for r in reservations}):
        selected = [r for r in reservations if r["account"] == account]
        requests = [
            {"custom_id": i["custom_id"], "params": i["params"]}
            for i in job["items"]
            if i["custom_id"] in {r["custom_id"] for r in selected}
        ]
        for reservation in selected:
            ledger.uncertain(reservation["token"])
        # No hidden retries: a lost create response must be reconciled in the console.
        with Anthropic(
            api_key=keys[account.split(":", 1)[1]],
            max_retries=0,
            timeout=config.request_timeout_seconds,
        ) as client:
            try:
                batch = client.messages.batches.create(requests=requests)  # type: ignore[arg-type]
            except Exception as error:
                save_json(
                    directory / f"uncertain-{len(receipts)}.json",
                    {"account": account, "error_type": type(error).__name__},
                )
                attempted_accounts = {account, *(receipt["account"] for receipt in receipts)}
                for reservation in reservations:
                    if reservation["account"] not in attempted_accounts:
                        ledger.settle(reservation["token"], 0, "not_submitted", None)
                raise RuntimeError(
                    "Batch creation response is uncertain; inspect provider console before retrying"
                ) from None
        receipt = {
            "id": batch.id,
            "account": account,
            "custom_ids": [r["custom_id"] for r in selected],
        }
        save_json(directory / f"batch-{len(receipts)}.json", receipt)
        receipts.append(receipt)


def recover(directory: Path, batch_id: str, key_env: str) -> None:
    """Attach a confirmed console batch ID after a lost create response; never resubmit."""
    job = load_json(directory / "job.json")
    config = RunConfig.model_validate(job["config"])
    account = "anthropic:" + key_env
    keys = credentials(profile_for(config))
    reservations = load_json(directory / "reservations.json")
    selected = [r for r in reservations if r["account"] == account]
    receipts = [load_json(p) for p in sorted(directory.glob("batch-*.json"))]
    with BudgetLedger(Path(job["ledger"]), config.total_budget_usd).locked() as state:
        creation_unconfirmed = bool(selected) and all(
            state["requests"].get(item["token"], {}).get("status") == "uncertain"
            for item in selected
        )
    if (
        not selected
        or key_env not in keys
        or not creation_unconfirmed
        or any(r["account"] == account or r["id"] == batch_id for r in receipts)
    ):
        raise ValueError("Select a configured account with an unconfirmed batch creation")
    with Anthropic(
        api_key=keys[key_env], max_retries=0, timeout=config.request_timeout_seconds
    ) as client:
        batch = client.messages.batches.retrieve(batch_id)
    if sum(batch.request_counts.model_dump().values()) != len(selected):
        raise ValueError("Provider batch request count differs from the reserved requests")
    save_json(
        directory / f"batch-{len(receipts)}.json",
        {
            "id": batch.id,
            "account": account,
            "custom_ids": [r["custom_id"] for r in selected],
            "recovered_from_console": True,
        },
    )


def apply_results(job: dict[str, Any], results: list[dict[str, Any]]) -> dict[str, Any]:
    output: dict[str, Any] = copy.deepcopy(job["bundle"])
    by_id = {item["custom_id"]: item for item in job["items"]}
    received: dict[str, dict[str, Any]] = {}
    for result in results:
        cid = result["custom_id"]
        if cid not in by_id or cid in received:
            raise ValueError("Batch returned an unknown or duplicate custom_id")
        received[cid] = result["result"]
    for item in job["items"]:
        run = next(r for r in output["runs"] if r["id"] == item["run_id"])
        case = next(c for c in run["cases"] if c["id"] == item["case_id"])
        for key in {"judge_error", "judge_record", "judge_summary", "judge_metrics"}:
            case.pop(key, None)
        result = received.get(item["custom_id"], {"type": "missing"})
        case.update(judge_status="error", judge=[])
        if result["type"] == "succeeded":
            try:
                blocks = [
                    b
                    for b in result["message"]["content"]
                    if b["type"] == "tool_use" and b["name"] == "submit_review"
                ]
                if len(blocks) != 1:
                    raise ValueError("Expected exactly one structured review")
                review = validated_review(
                    JudgeResult.model_validate(blocks[0]["input"]),
                    item["payload"],
                    job["rubric"],
                    metrics={**result["message"]["usage"], "requests": 1},
                )
                case.update(review_fields(review))
            except ValueError as error:
                case["judge_error"] = str(error)
                if isinstance(error, InvalidReview):
                    case["judge_record"] = error.record
        else:
            case["judge_error"] = "Batch result: " + result["type"]
        case["batch_result"] = result
    for run in output["runs"]:
        run["manifest"]["evaluation_profile_hash"] = fingerprint(
            {
                "native": run["manifest"].get("evaluation_profile_hash"),
                "batch_judge": job["profile_hash"],
            }
        )
        run["manifest"]["batch_judge_profile"] = job["profile_hash"]
    return output


def collect(directory: Path, *, status_only: bool) -> int:
    if not status_only and (directory / "judged.json").exists():
        output = load_json(directory / "judged.json")
        render(output, directory / "report.html")
        return evaluation_status(output)
    job = load_json(directory / "job.json")
    config = RunConfig.model_validate(job["config"])
    raw_path = directory / "raw-results.json"
    if raw_path.exists() and not status_only:
        results = load_json(raw_path)
    else:
        keys = credentials(profile_for(config))
        receipts = [load_json(p) for p in sorted(directory.glob("batch-*.json"))]
        if not receipts:
            raise ValueError("No confirmed provider batch ID; reconcile submission first")
        results = []
        for receipt in receipts:
            with Anthropic(
                api_key=keys[receipt["account"].split(":", 1)[1]],
                max_retries=0,
                timeout=config.request_timeout_seconds,
            ) as client:
                batch = client.messages.batches.retrieve(receipt["id"])
                print(batch.model_dump_json(include={"id", "processing_status", "request_counts"}))
                if status_only:
                    continue
                if batch.processing_status != "ended":
                    raise ValueError(
                        "Batch still processing; collect later, never wait on Reality Test"
                    )
                results.extend(
                    result.model_dump() for result in client.messages.batches.results(batch.id)
                )
        if status_only:
            return 0
        save_json(raw_path, results)
    output = apply_results(job, results)
    ledger = BudgetLedger(Path(job["ledger"]), config.total_budget_usd)
    reservations = {r["custom_id"]: r for r in load_json(directory / "reservations.json")}
    for result in results:
        value = result["result"]
        if value["type"] == "succeeded":
            usage = value["message"]["usage"]
            inputs = sum(
                usage.get(k, 0) or 0
                for k in ["input_tokens", "cache_read_input_tokens", "cache_creation_input_tokens"]
            )
            cost = (
                inputs * float(config.input_price_per_million or 0)
                + usage["output_tokens"] * float(config.output_price_per_million or 0)
            ) / 2_000_000
            ledger.settle(
                reservations[result["custom_id"]]["token"],
                cost,
                "batch_configured_token_price_upper_bound",
                value["message"].get("id"),
            )
        elif value["type"] in {"errored", "canceled", "expired"}:
            ledger.settle(
                reservations[result["custom_id"]]["token"], 0, "batch_not_processed", None
            )
    save_json(directory / "judged.json", output)
    render(output, directory / "report.html")
    return evaluation_status(output)


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(prog="dwelly-bot experiment batch")
    parser.add_argument("action", choices=["prepare", "submit", "status", "collect", "recover"])
    parser.add_argument("directory", type=Path)
    parser.add_argument("--input", type=Path)
    parser.add_argument("--config", type=Path)
    parser.add_argument("--rubric", type=Path, default=ROOT / "rubrics/default.json")
    parser.add_argument("--batch-id")
    parser.add_argument("--key-env")
    args = parser.parse_args(argv)
    if args.action == "prepare":
        if not args.input or not args.config:
            parser.error("prepare requires --input and --config")
        prepare(
            load_json(args.input),
            args.config,
            args.directory,
            json.loads(args.rubric.read_text()),
        )
    elif args.action == "submit":
        submit(args.directory)
    elif args.action == "recover":
        if not args.batch_id or not args.key_env:
            parser.error(
                "recover requires --batch-id and --key-env from the original submission account"
            )
        recover(args.directory, args.batch_id, args.key_env)
    else:
        return collect(args.directory, status_only=args.action == "status")
    return 0
