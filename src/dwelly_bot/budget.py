"""Persistent process-safe spending reservations shared by every paid model role."""

from __future__ import annotations

import fcntl
import json
import math
import time
import uuid
from collections import Counter
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from typing import Any

from dwelly_bot.storage import save_json


class BudgetExceeded(RuntimeError):
    """No new request may start while the shared ceiling cannot cover it."""


class BudgetLedger:
    def __init__(self, path: Path, ceiling: float = 15) -> None:
        if not math.isfinite(ceiling) or not 0 < ceiling <= 10000:
            raise ValueError("Budget ceiling must be finite and between USD 0 and 10000")
        self.path = path
        self.ceiling = ceiling
        self.path.parent.mkdir(parents=True, exist_ok=True)

    @contextmanager
    def locked(self) -> Iterator[dict[str, Any]]:
        with self.path.with_suffix(".lock").open("a+") as lock:
            fcntl.flock(lock.fileno(), fcntl.LOCK_EX)
            state: dict[str, Any] = (
                json.loads(self.path.read_text())
                if self.path.exists()
                else {
                    "ceiling_usd": self.ceiling,
                    "requests": {},
                }
            )
            state["ceiling_usd"] = min(float(state["ceiling_usd"]), self.ceiling)
            try:
                yield state
            finally:
                save_json(self.path, state, overwrite=True)

    @staticmethod
    def exposure(state: dict[str, Any], account: str | None = None) -> float:
        return sum(
            float(row["cost_usd"])
            for row in state.get("carried_accounts", [])
            if account is None or row["account"] == account
        ) + sum(
            float(r["cost_usd"])
            for r in state["requests"].values()
            if account is None or r.get("account") == account
        )

    def carry_forward(self, destination: Path) -> None:
        """Remove settled request detail without releasing spend or pending reservations.

        Call only with paid workers stopped. The caller removes the old ledger after
        verifying the new summary. Pending tokens retain their reconciliation identity.
        """
        if destination.resolve() == self.path.resolve() or destination.exists():
            raise ValueError("Carry-forward destination must be new")
        with self.locked() as state:
            accounts = {row["account"]: dict(row) for row in state.get("carried_accounts", [])}
            pending = {}
            for token, request in state["requests"].items():
                if request["status"] != "settled":
                    pending[token] = {k: v for k, v in request.items() if k != "case_id"}
                    continue
                account = request.get("account")
                row = accounts.setdefault(
                    account,
                    {
                        "account": account,
                        "cost_usd": 0.0,
                        "reported_cost_usd": 0.0,
                        "request_count": 0,
                    },
                )
                row["cost_usd"] += request["cost_usd"]
                row["request_count"] += 1
                if request.get("cost_basis") == "provider_reported":
                    row["reported_cost_usd"] += request["cost_usd"]
            carried = {
                "ceiling_usd": state["ceiling_usd"],
                "carried_accounts": list(accounts.values()),
                "requests": pending,
                "account_cooldowns": state.get("account_cooldowns", {}),
            }
            if not math.isclose(self.exposure(state), self.exposure(carried), abs_tol=1e-10):
                raise ValueError("Carry-forward changed financial exposure")
            destination.parent.mkdir(parents=True, exist_ok=True)
            save_json(destination, carried)

    def reserve_account(
        self,
        upper_bound: float,
        model: str,
        case_id: str,
        accounts: dict[str, float] | None = None,
    ) -> tuple[str, str | None]:
        if not math.isfinite(upper_bound) or upper_bound <= 0:
            raise ValueError("Reservation must be a finite positive upper bound")
        with self.locked() as state:
            if self.exposure(state) + upper_bound > state["ceiling_usd"] - 0.01:
                raise BudgetExceeded("Shared budget ceiling cannot cover another request")
            account = None
            if accounts:
                exposure = {name: self.exposure(state, name) for name in accounts}
                eligible = [
                    name
                    for name in accounts
                    if exposure[name] + upper_bound <= accounts[name]
                    and state.get("account_cooldowns", {}).get(name, 0) <= time.time()
                ]
                if not eligible:
                    raise BudgetExceeded("No configured credential has enough local allowance")
                account = min(eligible, key=lambda name: (exposure[name], name))
            token = uuid.uuid4().hex
            state["requests"][token] = {
                "model": model,
                "case_id": case_id,
                "status": "reserved",
                "cost_usd": upper_bound,
                "reserved_usd": upper_bound,
                "account": account,
            }
        return token, account

    def settle(self, token: str, cost: float, basis: str, response_id: str | None) -> None:
        if not math.isfinite(cost) or cost < 0:
            raise ValueError("Reported cost must be finite and nonnegative")
        with self.locked() as state:
            request = state["requests"][token]
            settlement = dict(
                status="settled", cost_usd=cost, cost_basis=basis, response_id=response_id
            )
            if request["status"] == "settled" and any(
                request[key] != value for key, value in settlement.items()
            ):
                raise ValueError("Conflicting settlement for a confirmed request")
            request.update(settlement)

    def uncertain(self, token: str) -> None:
        # Timeout/network errors can still be billed: keep the complete reservation.
        with self.locked() as state:
            if state["requests"][token]["status"] == "settled":
                raise ValueError("A confirmed request cannot become uncertain")
            state["requests"][token]["status"] = "uncertain"

    def cooldown(self, account: str, seconds: float = 60) -> None:
        with self.locked() as state:
            state.setdefault("account_cooldowns", {})[account] = time.time() + seconds

    def summary(self) -> dict[str, Any]:
        with self.locked() as state:
            counts = Counter(r["status"] for r in state["requests"].values())
            return {
                "ceiling_usd": state["ceiling_usd"],
                "exposure_usd": self.exposure(state),
                "reported_cost_usd": sum(
                    r["cost_usd"]
                    for r in state["requests"].values()
                    if r.get("cost_basis") == "provider_reported"
                )
                + sum(r["reported_cost_usd"] for r in state.get("carried_accounts", [])),
                "request_count": len(state["requests"])
                + sum(r["request_count"] for r in state.get("carried_accounts", [])),
                "uncertain_requests": counts["uncertain"],
                "pending_requests": counts["reserved"],
                "accounts": {
                    name: self.exposure(state, name)
                    for name in {r.get("account") for r in state["requests"].values()}
                    | {r["account"] for r in state.get("carried_accounts", [])}
                    if name
                },
            }
