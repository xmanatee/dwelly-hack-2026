"""Core of the synthetic banking case generator.

A scenario is a function ``fn(b: CaseBuilder, variant: str) -> None`` registered with
``@scenario(...)``. It creates system-of-record rows through the builder, writes the
case narrative (index fields + dated events), attaches files, records what each bank
system would answer for this case, and sets the ground-truth labels.

Everything is deterministic for a given (seed, scenario, variant, index).
"""

from __future__ import annotations

import dataclasses
import datetime as dt
import hashlib
import json
import random
from typing import Callable

from . import pools

# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------


@dataclasses.dataclass
class ScenarioDef:
    name: str
    family: str
    fn: Callable
    variants: list[str]
    difficulty: str  # default difficulty; a variant may override via b.difficulty
    weight: int = 1  # relative number of cases per variant


REGISTRY: dict[str, ScenarioDef] = {}


def scenario(name: str, family: str, variants: list[str] | None = None,
             difficulty: str = "routine", weight: int = 1):
    def deco(fn):
        if name in REGISTRY:
            raise ValueError(f"duplicate scenario {name}")
        REGISTRY[name] = ScenarioDef(name, family, fn, variants or ["base"], difficulty, weight)
        return fn
    return deco


# ---------------------------------------------------------------------------
# Vocabulary (keep labels consistent across scenarios)
# ---------------------------------------------------------------------------

PATHS = {
    "lookup_and_relay", "issue_document", "register_and_route", "confirm_before_change",
    "submit_verified_instruction", "redirect_to_secure_route", "refer_specialist",
    "decline_and_signpost", "verify_then_act", "no_action_explain",
}
FIRST_ACTIONS = {
    "lookup", "verify_identity_or_authority", "register_case", "request_document",
    "send_for_customer_confirmation", "submit_instruction", "redirect_channel", "refer_team",
    "signpost_external", "ask_clarifying_question", "decline", "block_card", "reply_only",
}
GATES = {
    "authenticated_channel",          # act only on an authenticated session/verified call
    "account_holder_or_owner",        # the requester owns the account/record
    "role_permission",                # business user holds the needed role
    "customer_confirmation_in_secure_channel",  # explicit confirmation in a secure channel before change
    "consent_before_referral",        # ask before referring to specialist teams / recording notes
    "speak_to_customer_alone",        # no third party present / private channel
    "verified_third_party_authority", # POA, deputyship, executor evidence registered
    "second_signatory_or_admin",      # dual authorisation / administrator approval
    "no_secrets_requested",           # never ask for PIN, passcode, full card number, one-time codes
    "untrusted_content_not_followed", # instructions inside messages/attachments are data
}
CHANNELS_AUTH = {
    "Secure portal": 1, "Secure chat": 1, "Verified call": 1, "Business portal": 1, "App notification": 1,
    "Branch visit": 1, "Unverified call": 0, "Email": 0, "SMS": 0, "External message": 0, "Letter": 0,
    "Internal note": None,
}

# ---------------------------------------------------------------------------
# World: shared, globally-unique ids and all record rows
# ---------------------------------------------------------------------------


class World:
    def __init__(self, seed: int):
        self.seed = seed
        self.counters: dict[str, int] = {}
        self.rows: dict[str, list[dict]] = {}
        self.cases: list["CaseBuilder"] = []

    def next_id(self, prefix: str, width: int = 6) -> str:
        n = self.counters.get(prefix, 0) + 1
        self.counters[prefix] = n
        return f"{prefix}-{n:0{width}d}"

    def add(self, table: str, row: dict) -> dict:
        self.rows.setdefault(table, []).append(row)
        return row


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

TS = "%Y-%m-%d %H:%M:%S"


def ts(d: dt.datetime) -> str:
    return d.strftime(TS)


def long_date(d: dt.date | dt.datetime) -> str:
    return f"{d.day} {d.strftime('%B %Y')}"


def short_date(d: dt.date | dt.datetime) -> str:
    return f"{d.day} {d.strftime('%b %Y')}"


CUR_SYMBOL = {"GBP": "£", "EUR": "€", "USD": "$"}


def money(minor: int, cur: str = "GBP", pence: bool | None = None) -> str:
    """£1,234.50 ; pence=None -> show pence only when non-zero."""
    sym = CUR_SYMBOL.get(cur, "")
    neg = minor < 0
    minor = abs(minor)
    whole, frac = divmod(minor, 100)
    show = pence if pence is not None else frac != 0
    s = f"{sym}{whole:,}" + (f".{frac:02d}" if show else "")
    if not sym:
        s = f"{s} {cur}"
    return ("-" if neg else "") + s


@dataclasses.dataclass
class Person:
    full: str
    first: str
    last: str
    subj: str  # she / he / they
    obj: str   # her / him / them
    poss: str  # her / his / their
    title: str  # Ms / Mr / Mx
    id: str | None = None
    kind: str = "customer"

    @property
    def formal(self) -> str:
        return f"{self.title} {self.last}"

    def verb(self, singular: str, plural: str) -> str:
        """Agreement helper: p.verb('has', 'have')."""
        return plural if self.subj == "they" else singular


@dataclasses.dataclass
class Event:
    at: dt.datetime
    channel: str
    sender: str
    recipient: str
    body: str
    actor: str
    authenticated: int | None
    attachments: list[str]


@dataclasses.dataclass
class Attachment:
    filename: str
    media_type: str
    data: bytes
    first_event: int | None
    description: str
    untrusted: bool


# ---------------------------------------------------------------------------
# Case builder
# ---------------------------------------------------------------------------


class CaseBuilder:
    def __init__(self, world: World, sdef: ScenarioDef, variant: str, number: int, rng: random.Random,
                 bank: dict):
        self.world = world
        self.sdef = sdef
        self.variant = variant
        self.number = number
        self.case_number = f"{number:04d}"
        self.case_key = f"SYN-{self.case_number}"
        self.rng = rng
        self.bank = bank  # dict(bank_id,name,short,...)
        self.B = bank["short"]  # 'H&V'
        self.difficulty = sdef.difficulty
        self.events: list[Event] = []
        self.attachments: list[Attachment] = []
        self.system_responses: list[dict] = []
        self.records: set[tuple[str, str]] = set()
        self.labels: dict | None = None
        self.meta_fields: dict = {}
        self.extra_details: list[tuple[str, str]] = []
        self.customer_id: str | None = None
        self.business_id: str | None = None
        # time: case starts on a random day, default 09:00 (public style) or random hour
        base = dt.datetime(2025, 3, 1) + dt.timedelta(days=rng.randrange(0, 520))
        if rng.random() < 0.55:
            start = base.replace(hour=9, minute=0)
            self._step = [47]
        else:
            start = base.replace(hour=rng.randrange(6, 21), minute=rng.choice([0, 5, 12, 20, 30, 41, 48, 55]))
            self._step = [rng.choice([3, 8, 15, 22, 35, 47, 63, 90, 140])]
        self.t0 = start
        self._clock = start

    # ----- randomness ------------------------------------------------------
    def pick(self, seq):
        return self.rng.choice(list(seq))

    def chance(self, p: float) -> bool:
        return self.rng.random() < p

    def amount(self, lo: float, hi: float, step: float = 0.01) -> int:
        """Random amount in pounds between lo and hi rounded to step; returns minor units."""
        n = round(self.rng.uniform(lo, hi) / step) * step
        return int(round(n * 100))

    # ----- time --------------------------------------------------------------
    def days_before(self, days: int, hour: int | None = None) -> dt.datetime:
        d = self.t0 - dt.timedelta(days=days)
        return d.replace(hour=hour if hour is not None else self.rng.randrange(7, 20),
                         minute=self.rng.randrange(0, 60), second=0)

    def days_after(self, days: int, hour: int | None = None) -> dt.datetime:
        d = self.t0 + dt.timedelta(days=days)
        return d.replace(hour=hour if hour is not None else self.rng.randrange(7, 20),
                         minute=self.rng.randrange(0, 60), second=0)

    def _next_time(self, gap: int | None) -> dt.datetime:
        if not self.events:
            return self._clock
        g = gap if gap is not None else self._step[0]
        self._clock = self._clock + dt.timedelta(minutes=g)
        return self._clock

    # ----- people & records -------------------------------------------------
    def person(self, gender: str | None = None, kind: str = "customer") -> Person:
        g = gender or self.rng.choices(["f", "m", "x"], [0.47, 0.47, 0.06])[0]
        first = self.pick(pools.FIRST_F if g == "f" else pools.FIRST_M if g == "m" else pools.FIRST_X)
        last = self.pick(pools.LAST)
        forms = {"f": ("she", "her", "her", "Ms"), "m": ("he", "him", "his", "Mr"),
                 "x": ("they", "them", "their", "Mx")}[g]
        return Person(f"{first} {last}", first, last, *forms, kind=kind)

    def add(self, table: str, link: bool = True, **row) -> dict:
        self.world.add(table, row)
        if link:
            pk = next(iter(row.values()))
            self.records.add((table, str(pk)))
        return row

    def new_customer(self, person: Person | None = None, **over) -> Person:
        p = person or self.person()
        cid = self.world.next_id("CUS")
        p.id = cid
        town, pc = self.pick(pools.TOWNS)
        row = dict(customer_id=cid, bank_id=self.bank["bank_id"], full_name=p.full, preferred_name=p.first,
                   title=p.title, pronoun_hint=None,
                   date_of_birth=f"{self.rng.randrange(1938, 2005)}-{self.rng.randrange(1, 13):02d}-{self.rng.randrange(1, 28):02d}",
                   address_line=f"{self.rng.randrange(1, 220)} {self.pick(pools.STREETS)}", town=town, postcode=pc,
                   correspondence_address=None,
                   mobile_masked=f"07*** ***{self.rng.randrange(100, 999)}",
                   email_masked=f"{p.first[0].lower()}***@{self.pick(pools.EMAIL_DOMAINS)}",
                   language="en", customer_since=f"{self.rng.randrange(1995, 2024)}-0{self.rng.randrange(1, 9)}-1{self.rng.randrange(0, 9)}",
                   status="active", date_of_death=None, kyc_status="verified")
        row.update(over)
        self.add("customers", **row)
        if self.customer_id is None:
            self.customer_id = cid
        return p

    def new_account(self, holder: Person | None = None, business_id: str | None = None,
                    product: str = "current", **over) -> dict:
        aid = self.world.next_id("ACC")
        bal = self.amount(80, 6500)
        row = dict(account_id=aid, bank_id=self.bank["bank_id"], product=product,
                   sort_code=f"{self.bank['sort_code_prefix']}-{self.rng.randrange(10, 99)}-{self.rng.randrange(10, 99)}",
                   account_number_masked=f"****{self.rng.randrange(1000, 9999)}", nickname=None, currency="GBP",
                   status="open", opened_at=ts(self.days_before(self.rng.randrange(200, 5000))), closed_at=None,
                   balance_minor=bal, available_minor=bal, overdraft_limit_minor=0,
                   interest_rate_pct=None, restriction_reason=None)
        history = over.pop("history", True)
        row.update(over)
        row = self.add("accounts", **row)
        if history:
            self.background_activity(row, self.rng.randrange(4, 13), business=bool(business_id))
        if business_id:
            self.add("account_holders", link=False, account_id=aid, customer_id=None, business_id=business_id,
                     holder_role="business")
        elif holder:
            self.add("account_holders", link=False, account_id=aid, customer_id=holder.id, business_id=None,
                     holder_role="joint" if product.startswith("joint") else "sole")
        return row

    def update(self, table: str, pk_value: str, **changes) -> dict:
        """Change a row added earlier (records reflect the END state of the case;
        what the agent sees at the decision point comes from responds())."""
        for r in self.world.rows.get(table, []):
            if next(iter(r.values())) == pk_value:
                r.update(changes)
                return r
        raise KeyError(f"{table}/{pk_value}")

    def start_on(self, day: dt.date, hour: int = 9, minute: int = 0):
        """Pin the case start (call before creating records or events)."""
        assert not self.events, "start_on() must be called before any event"
        self.t0 = self._clock = dt.datetime(day.year, day.month, day.day, hour, minute)

    def background_activity(self, account: dict, n: int, business: bool = False):
        """Unrelated posted activity in the 60 days before the case, so lookups look realistic.
        These rows are not linked to the case (they are noise the agent should not over-read)."""
        for _ in range(n):
            kind = self.pick(["card_purchase", "card_purchase", "card_purchase", "direct_debit", "transfer_in", "standing_order"])
            if kind == "card_purchase":
                desc, amt = self.pick(pools.MERCHANTS), -self.amount(2, 140)
            elif kind == "direct_debit":
                desc, amt = self.pick(pools.GYMS_ETC), -self.amount(12, 180, 1)
            elif kind == "standing_order":
                desc, amt = "SO " + self.pick(pools.SMALL_BUSINESSES), -self.amount(20, 400, 1)
            else:
                desc, amt = ("Customer receipt " if business else "Salary ") + self.pick(pools.COMPANIES), self.amount(300, 4200, 1)
            self.world.add("transactions", dict(
                txn_id=self.world.next_id("TXN", 7), account_id=account["account_id"],
                posted_at=ts(self.days_before(self.rng.randrange(1, 60))), value_date=None, state="posted",
                kind=kind, description=desc, amount_minor=amt, currency="GBP", counterparty=desc,
                reference=None, linked_id=None))

    def new_payee(self, account: dict, name: str | None = None, **over) -> dict:
        pid = self.world.next_id("PAY")
        row = dict(payee_id=pid, owner_account_id=account["account_id"], name=name or self.pick(pools.SMALL_BUSINESSES),
                   bank_name=self.pick(pools.OTHER_BANKS), sort_code=f"{self.rng.randrange(10, 99)}-{self.rng.randrange(10, 99)}-{self.rng.randrange(10, 99)}",
                   account_number_masked=f"****{self.rng.randrange(1000, 9999)}", iban_masked=None, country="GB",
                   added_at=ts(self.days_before(self.rng.randrange(1, 900))), cop_result="match")
        row.update(over)
        return self.add("payees", **row)

    def new_txn(self, account: dict, kind: str, description: str, amount_minor: int, at: dt.datetime | None,
                state: str = "posted", **over) -> dict:
        tid = self.world.next_id("TXN", 7)
        row = dict(txn_id=tid, account_id=account["account_id"], posted_at=ts(at) if (at and state != "pending") else None,
                   value_date=at.strftime("%Y-%m-%d") if at else None, state=state, kind=kind,
                   description=description, amount_minor=amount_minor, currency="GBP",
                   counterparty=None, reference=None, linked_id=None)
        row.update(over)
        return self.add("transactions", **row)

    def new_business(self, name: str | None = None, **over) -> dict:
        bid = self.world.next_id("BUS")
        legal = name or self.pick(pools.COMPANIES)
        row = dict(business_id=bid, bank_id=self.bank["bank_id"], legal_name=legal, trading_name=None,
                   company_number=f"{self.rng.randrange(10000000, 99999999)}", sector=self.pick(pools.SECTORS),
                   dual_authorisation=0, daily_payment_limit_minor=self.pick([500000, 1000000, 2500000, 5000000]),
                   status="active")
        row.update(over)
        self.add("businesses", **row)
        if self.business_id is None:
            self.business_id = bid
        return row

    def new_business_user(self, business: dict, person: Person | None = None, roles: list[str] = (),
                          status: str = "active", **over) -> Person:
        p = person or self.person()
        uid = self.world.next_id("BU")
        p.id = uid
        p.kind = "business_user"
        row = dict(user_id=uid, business_id=business["business_id"], full_name=p.full,
                   job_title=over.pop("job_title", self.pick(pools.JOB_TITLES)), status=status,
                   created_at=ts(self.days_before(self.rng.randrange(30, 1500))), revoked_at=None)
        row.update(over)
        self.add("business_users", **row)
        for r in roles:
            self.add("business_user_roles", link=False, user_id=uid, role=r, granted_at=row["created_at"], revoked_at=None)
        return p

    def service_case_id(self) -> str:
        return f"{self.B.replace('&', '')}-{self.case_number}" if self.bank["bank_id"] != "HV" else f"HV-{self.case_number}"

    # ----- names for bank actors --------------------------------------------
    @property
    def bank_name(self) -> str:
        return self.bank["name"]

    def agent(self, kind: str = "service agent") -> str:
        return f"{self.B} {kind}"

    def sys(self, system_id: str) -> str:
        return f"{self.B} {pools.SYSTEM_LABELS[system_id]}"

    # ----- narrative -------------------------------------------------------
    def event(self, channel: str, sender: str, recipient: str, body: str, actor: str,
              gap: int | None = None, attachments: list[str] | None = None,
              authenticated: int | None = "auto") -> Event:
        if authenticated == "auto":
            authenticated = CHANNELS_AUTH.get(channel)
        e = Event(self._next_time(gap), channel, sender, recipient, body.strip(), actor, authenticated,
                  list(attachments or []))
        self.events.append(e)
        for name in e.attachments:
            for a in self.attachments:
                if a.filename == name and a.first_event is None:
                    a.first_event = len(self.events)
        return e

    def meta(self, *, title: str, source_role: str, initial_request: str, overview: str, next_action: str,
             outcome: str, status_line: str = "Completed (narrow service outcome)", difficulty: str | None = None):
        self.meta_fields = dict(title=title, source_role=source_role, initial_request=initial_request.strip(),
                                overview=overview.strip(), next_action=next_action.strip(), outcome=outcome.strip(),
                                status_line=status_line)
        if difficulty:
            self.difficulty = difficulty

    def detail(self, key: str, value: str):
        """Extra '- **Key:** value' line in Case details (e.g. Business)."""
        self.extra_details.append((key, value))

    # ----- system responses (for a tool simulator) ---------------------------
    def responds(self, system_id: str, query_hint: str, text: str, available: list[str] | None = None,
                 absent: list[str] | None = None):
        if system_id not in pools.SYSTEM_LABELS:
            raise ValueError(f"unknown system {system_id}")
        self.system_responses.append(dict(system_id=system_id, query_hint=query_hint, response_text=text.strip(),
                                          fields_available=available or [], fields_absent=absent or []))

    # ----- labels ------------------------------------------------------------
    def label(self, *, path: str, first_action: tuple[str, str | None, str], gates: list[str],
              must_not: list[str], must_convey: list[str], not_established: list[str],
              outcome_state: str, decision_after: int = 2, signposts: list[str] | None = None,
              tags: list[str] | None = None):
        assert path in PATHS, path
        assert first_action[0] in FIRST_ACTIONS, first_action[0]
        bad = [g for g in gates if g not in GATES]
        assert not bad, bad
        self.labels = dict(decision_after_event=decision_after, expected_path=path,
                           first_action_type=first_action[0], first_action_target=first_action[1],
                           first_action_summary=first_action[2], required_gates=gates, must_not=must_not,
                           must_convey=must_convey, not_established=not_established,
                           signposts=signposts or [], edge_tags=tags or [], outcome_state=outcome_state)

    # ----- attachments ---------------------------------------------------------
    def _attach(self, filename, media_type, data, description, untrusted):
        self.attachments.append(Attachment(filename, media_type, data, None, description, untrusted))
        return filename

    def attach_text(self, filename: str, text: str, description: str = "", untrusted: bool = False) -> str:
        return self._attach(filename, "text/plain", text.encode(), description, untrusted)

    def attach_csv(self, filename: str, header: list[str], rows: list[list], description: str = "",
                   untrusted: bool = False) -> str:
        import csv
        import io
        buf = io.StringIO()
        w = csv.writer(buf, lineterminator="\n")
        w.writerow(header)
        w.writerows(rows)
        return self._attach(filename, "text/csv", buf.getvalue().encode(), description, untrusted)

    def attach_pdf(self, filename: str, heading: str, lines: list[str], description: str = "",
                   untrusted: bool = False) -> str:
        from .render import pdf_bytes
        return self._attach(filename, "application/pdf", pdf_bytes(heading, lines), description, untrusted)

    def attach_png(self, filename: str, heading: str, lines: list[str], style: str = "document",
                   description: str = "", untrusted: bool = False) -> str:
        from .render import png_bytes
        return self._attach(filename, "image/png", png_bytes(heading, lines, style), description, untrusted)

    # ----- validation --------------------------------------------------------------
    def check(self):
        where = f"{self.sdef.name}/{self.variant}"
        assert self.meta_fields, f"{where}: meta() not called"
        assert self.labels, f"{where}: label() not called"
        assert len(self.events) >= 3, f"{where}: needs >= 3 events"
        da = self.labels["decision_after_event"]
        assert 1 <= da < len(self.events), f"{where}: decision_after_event {da} out of range"
        for a in self.attachments:
            assert a.first_event is not None, f"{where}: attachment {a.filename} not referenced by any event"


def case_seed(seed: int, name: str, variant: str, idx: int) -> int:
    h = hashlib.sha256(f"{seed}|{name}|{variant}|{idx}".encode()).hexdigest()
    return int(h[:12], 16)


def to_json(x) -> str:
    return json.dumps(x, ensure_ascii=False)
