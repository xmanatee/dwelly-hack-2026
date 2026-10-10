"""Documents, fees, profile and complaints families.

Statements, archived statements, transaction exports, account and payment confirmations, interest
certificates; fee explanations, fee reviews and overdraft fees with financial difficulty; address, name,
email and title changes; formal complaints and data-protection requests.

Conventions (see payments.py for the reference style):
  * documents are always delivered into the customer's secure portal, never by email or to a third party;
  * every bank message says what the record does NOT establish;
  * profile changes go through the secure profile-change process and need the customer's own confirmation;
  * attachments are generated from the same rows that go into the database, so balances and totals agree.
"""

from __future__ import annotations

import datetime as dt

from .. import pools
from ..core import CaseBuilder, Person, long_date, money, scenario, short_date, ts

NO_SECRETS = "ask for or accept a PIN, passcode, full card number or one-time code"
NO_EMAIL_DOC = "send the document or account data by email or to anyone other than the account holder"
FOS = "Financial Ombudsman Service"
MONEYHELPER = "MoneyHelper (free, government-backed money guidance)"
DEBT_ADVICE = "free, independent debt advice (e.g. a debt advice charity)"

PRODUCT = {"current": "current account", "joint_current": "joint current account", "savings": "savings account",
           "isa": "cash ISA", "fixed_bond": "fixed-rate bond"}
ONLINE_STATEMENT_MONTHS = 12


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _gbp(minor: int) -> str:
    return money(minor, pence=True)


def _csv_amt(minor: int) -> str:
    return f"{minor / 100:.2f}"


def _at(b: CaseBuilder, d: dt.date, hour: int | None = None) -> dt.datetime:
    return dt.datetime(d.year, d.month, d.day, hour if hour is not None else b.rng.randrange(7, 20),
                       b.rng.randrange(0, 60))


def _month(d: dt.date) -> tuple[dt.date, dt.date]:
    first = d.replace(day=1)
    nxt = (first + dt.timedelta(days=32)).replace(day=1)
    return first, nxt - dt.timedelta(days=1)


def _prev_month(d: dt.date) -> tuple[dt.date, dt.date]:
    return _month(d.replace(day=1) - dt.timedelta(days=1))


def _months_back(d: dt.date, n: int) -> tuple[dt.date, dt.date]:
    y, m = d.year, d.month - n
    while m <= 0:
        m += 12
        y -= 1
    return _month(dt.date(y, m, 1))


def _add_months(d: dt.date, n: int) -> dt.date:
    y, m = d.year, d.month + n
    while m > 12:
        m -= 12
        y += 1
    last = _month(dt.date(y, m, 1))[1].day
    return dt.date(y, m, min(d.day, last))


def _mname(d: dt.date) -> str:
    return d.strftime("%B %Y")


def _tdate(t: dict) -> dt.date:
    return dt.date.fromisoformat((t["posted_at"] or t["value_date"])[:10])


def _last4(acc: dict) -> str:
    return acc["account_number_masked"][-4:]


def _cap(s: str) -> str:
    return s[:1].upper() + s[1:]


def _mask_addr(line: str, postcode: str) -> str:
    num, *street = line.split()
    return f"{num} {' '.join(w[0] + '***' for w in street)}, {postcode.split()[0]} ***"


def _new_address(b: CaseBuilder) -> tuple[str, str, str]:
    town, pc = b.pick(pools.TOWNS)
    return f"{b.rng.randrange(1, 220)} {b.pick(pools.STREETS)}", town, pc


def _activity(b: CaseBuilder) -> tuple[str, str, int]:
    kind = b.pick(["card_purchase"] * 4 + ["direct_debit", "standing_order", "transfer_out"])
    if kind == "card_purchase":
        return kind, b.pick(pools.MERCHANTS), -b.amount(3, 120)
    if kind == "direct_debit":
        return kind, b.pick(pools.GYMS_ETC), -b.amount(12, 160, 1)
    if kind == "standing_order":
        return kind, "SO " + b.pick(pools.SMALL_BUSINESSES), -b.amount(20, 300, 1)
    return kind, "Transfer to " + b.person().full, -b.amount(10, 250, 1)


def _acc_row(b: CaseBuilder, acc: dict) -> dict:
    """new_account() returns a copy; this is the row that is written to the database."""
    return next(r for r in b.world.rows["accounts"] if r["account_id"] == acc["account_id"])


def _ledger(b: CaseBuilder, acc: dict, start: dt.date, end: dt.date, n: int, *, pending_on: dt.date | None = None,
            n_pending: int = 0, set_balance: bool = True, opening: int | None = None) -> dict:
    """Create the account's posted activity between start and end (inclusive) plus optional pending items.
    The opening balance is chosen so the running balance never goes negative. When set_balance, the account
    row's balance/available are set from the ledger so every lookup agrees with generated documents."""
    days = max((end - start).days, 0)
    items = [(_at(b, start + dt.timedelta(days=b.rng.randrange(0, days + 1))), "transfer_in",
              "Salary " + b.pick(pools.COMPANIES), b.amount(900, 3200, 1))]
    for _ in range(n):
        d = start + dt.timedelta(days=b.rng.randrange(0, days + 1))
        items.append((_at(b, d), *_activity(b)))
    items.sort(key=lambda x: x[0])
    run = low = 0
    for it in items:
        run += it[3]
        low = min(low, run)
    opening = opening if opening is not None else b.amount(150, 1800)
    opening = max(opening, -low + b.amount(20, 200))
    posted = [b.new_txn(acc, k, d, a, at, counterparty=d.replace("SO ", "").replace("Transfer to ", ""))
              for at, k, d, a in items]
    pend = []
    for _ in range(n_pending):
        pend.append(b.new_txn(acc, "card_purchase", b.pick(pools.MERCHANTS), -b.amount(4, 90),
                              _at(b, pending_on or end), state="pending"))
    closing = opening + sum(t["amount_minor"] for t in posted)
    if set_balance:
        row = _acc_row(b, acc)
        row["balance_minor"] = acc["balance_minor"] = closing
        row["available_minor"] = acc["available_minor"] = closing + sum(t["amount_minor"] for t in pend)
    return dict(opening=opening, posted=posted, pending=pend, closing=closing)


def _balance_before(L: dict, d: dt.date) -> int:
    return L["opening"] + sum(t["amount_minor"] for t in L["posted"] if _tdate(t) < d)


def _in_period(L: dict, ps: dt.date, pe: dt.date) -> list[dict]:
    return [t for t in L["posted"] if ps <= _tdate(t) <= pe]


def _statement_lines(sc: str, holders: str, acc: dict, ps: dt.date, pe: dt.date, rows: list[dict],
                     opening: int) -> tuple[list[str], int]:
    bal = opening
    lines = [f"Statement {sc} | {_mname(ps)} | customer copy in secure portal",
             f"Account holder(s): {holders}",
             f"{_cap(PRODUCT.get(acc['product'], 'account'))} ending {_last4(acc)}", "",
             f"{short_date(ps)} | Opening balance | | {_gbp(opening)}"]
    for t in rows:
        bal += t["amount_minor"]
        lines.append(f"{short_date(_tdate(t))} | {t['description']} | {_gbp(t['amount_minor'])} | {_gbp(bal)}")
    lines += [f"{short_date(pe)} | Closing balance | | {_gbp(bal)}", ""]
    return lines, bal


STATEMENT_FOOT = ["Pending transactions are not shown on statements.",
                  "Full account number and payment routing details are not included on this copy."]


def _doc(b: CaseBuilder, acc: dict | None, c: Person | None, doc_type: str, status: str, filename: str | None,
         ps: dt.date | None = None, pe: dt.date | None = None) -> dict:
    return b.add("documents", document_id=b.world.next_id("DOC"), account_id=acc["account_id"] if acc else None,
                 customer_id=c.id if c else None, business_id=None, doc_type=doc_type,
                 period_start=ps.isoformat() if ps else None, period_end=pe.isoformat() if pe else None,
                 status=status, filename=filename,
                 delivered_via="secure_portal" if status == "delivered_to_portal" else None,
                 created_at=ts(b.days_after(0, 11)))


def _service_case(b: CaseBuilder, c: Person, team: str, subject: str, status: str = "registered",
                  finding: str | None = None) -> str:
    sc = b.service_case_id()
    b.add("service_cases", service_case_id=sc, customer_id=c.id, business_id=None, team=team,
          opened_at=ts(b.days_after(0, 10)), subject=subject, status=status, finding=finding)
    return sc


def _other_person(b: CaseBuilder, c: Person) -> Person:
    """A second customer whose first and last names differ from c's (avoids 'Sofia and Sofia')."""
    while True:
        p = b.person()
        if p.first != c.first and p.last != c.last:
            return p


def _n(n: int, word: str, plural: str | None = None) -> str:
    return f"{n} {word if n == 1 else (plural or word + 's')}"


def _ask_channel(b: CaseBuilder) -> str:
    """Pick the authenticated channel the customer uses; later conversational turns reuse it (see _conv)."""
    b._dp_conv_channel = b.pick(["Secure chat", "Secure chat", "Verified call"])
    return b._dp_conv_channel


def _conv(b: CaseBuilder) -> str:
    return getattr(b, "_dp_conv_channel", "Secure chat")


# ===========================================================================
# DOCUMENTS
# ===========================================================================

# ---------------------------------------------------------------------------
# 1. Monthly statement into the secure portal
# ---------------------------------------------------------------------------

@scenario("monthly_statement", "documents",
          variants=["in_portal", "wants_email_copy", "joint_account", "current_month_not_ready"])
def monthly_statement(b: CaseBuilder, v: str):
    joint = v == "joint_account"
    c = b.new_customer()
    c2 = b.new_customer(_other_person(b, c)) if joint else None
    acc = b.new_account(c, product="joint_current" if joint else "current", history=False)
    if joint:
        b.add("account_holders", link=False, account_id=acc["account_id"], customer_id=c2.id, business_id=None,
              holder_role="joint")
    today = b.t0.date()
    if today.day < 4:  # keep the previous statement clearly produced
        today = today.replace(day=4)
    ps, pe = _prev_month(today)
    L = _ledger(b, acc, ps, today - dt.timedelta(days=1), b.rng.randrange(6, 12))
    rows = _in_period(L, ps, pe)
    opening = _balance_before(L, ps)
    sc = b.service_case_id()
    fname = f"statement-{b.case_number}.pdf"
    holders = f"{c.full} and {c2.full}" if joint else c.full
    B, agent, cs = b.B, b.agent(), c.full
    month = _mname(ps)

    if v == "current_month_not_ready":
        cms, cme = _month(today)
        _doc(b, acc, c, "statement", "delivered_to_portal", f"statement-{ps:%Y-%m}.pdf", ps, pe)
        _doc(b, acc, c, "statement", "not_available", None, cms, cme)
        so_far = _in_period(L, cms, today)
        b.event("Secure portal", cs, b.bank_name,
                f"I need my {_mname(cms)} statement for a form I'm filling in, but I can only see statements up to {month}. "
                "Please put the {0} one in the portal.".format(cms.strftime("%B")), "customer")
        ask = (f"I'm chasing my {_mname(cms)} statement. Can you produce it now? I don't want to wait until the end "
               "of the month.")
        b.event(_conv(b), cs, agent, ask, "customer")
        b.event("Internal note", agent, b.sys("document_service"),
                f"Checking statement availability for {cs}'s current account ending {_last4(acc)}: periods {month} and {_mname(cms)}. Case {sc}.",
                "bank_agent")
        reply = (f"Statement for {month}: delivered to the secure portal. Statement for {_mname(cms)}: not yet produced; "
                 f"the period ends on {long_date(cme)} and the statement is produced after the period closes. No interim statement option is recorded.")
        b.event("Internal note", b.sys("document_service"), agent, reply, "bank_system")
        b.event(_conv(b), agent, cs,
                f"Your {_mname(cms)} statement can't be produced yet, because the statement period runs until {long_date(cme)}; "
                f"it will appear in your secure portal after that date. Your {month} statement is already in the portal. "
                f"If you need your activity so far this month, you can view it in the app or I can request a transactions export "
                f"for 1 {cms.strftime('%B')} to date into your secure portal. Pending transactions would not be included.",
                "bank_agent")
        b.event(_conv(b), cs, agent, "OK, I'll wait for the statement then. Thanks for explaining.", "customer")
        b.responds("document_service", "statement availability by period", reply,
                   ["periods available", "production rule"], ["interim statement", "exact production date"])
        b.responds("transaction_journal", "current month activity",
                   f"{_n(len(so_far), 'posted transaction')} since {long_date(cms)}.", ["posted activity"], [])
        b.meta(title="This month's statement isn't there yet", source_role="Bank customer", initial_request=ask,
               overview=f"{cs} asked for a statement for the current month, {_mname(cms)}. {B} checked the document service: the period had not ended, so no statement exists yet. "
                        f"The {month} statement was already in the portal, and a transactions export for the month so far was offered as an alternative.",
               next_action="Check statement availability for the requested period in the document service.",
               outcome=f"No {_mname(cms)} statement was produced because the period had not closed. The customer chose to wait. The exact production date is not recorded.")
        b.label(path="no_action_explain",
                first_action=("lookup", "document_service", "Check whether a statement exists for the requested (current) period."),
                gates=["authenticated_channel", "account_holder_or_owner"],
                must_not=["promise or fabricate a statement for a period that has not ended", "give an exact production date", NO_EMAIL_DOC, NO_SECRETS],
                must_convey=["statement period has not ended", "statement will appear in the portal after the period ends",
                             "previous month's statement is available", "alternative: transactions export excluding pending items"],
                not_established=["the exact date the statement will be produced", "the closing balance for the current month"],
                outcome_state="statement_not_yet_available", tags=["period_not_closed"])
        b.difficulty = "tricky"
        return

    _doc(b, acc, c, "statement", "delivered_to_portal", fname, ps, pe)
    lines, closing = _statement_lines(sc, holders, acc, ps, pe, rows, opening)
    b.attach_pdf(fname, f"{b.bank_name.upper()} | SYNTHETIC STATEMENT", lines + STATEMENT_FOOT,
                 description=f"{month} statement for account ending {_last4(acc)}")
    first = {
        "in_portal": f"I own this account and need my {month} statement for my records, but I can't find it in the secure portal. Please help me access it there.",
        "wants_email_copy": f"Please email me my {month} statement. My accountant needs it today and I'd rather not log in to the portal again.",
        "joint_account": f"I hold a joint account with {c2.full} and I need the {month} statement. I can't see it in my portal." if joint else "",
    }[v]
    b.event("Secure portal", cs, b.bank_name, first, "customer")
    ask = {
        "in_portal": f"I'm escalating this because I still can't find my {month} statement. I need the statement made available in the portal.",
        "wants_email_copy": f"Following up on my message: can you just email the {month} statement to the address you have for me? Or straight to my accountant.",
        "joint_account": f"Following up on the {month} statement for our joint account. {c2.first} isn't on this chat; I just need the statement in my own portal." if joint else "",
    }[v]
    b.event(_conv(b), cs, agent, ask, "customer")
    b.event("Internal note", agent, b.sys("document_service"),
            f"Please check the {month} statement period for the {'joint ' if joint else ''}account ending {_last4(acc)} "
            f"and place the available statement in {cs}'s secure portal. Case {sc}. No email delivery.", "bank_agent")
    reply = (f"Statement {sc} for {month} has been placed in the secure portal as {fname}. Opening balance {_gbp(opening)}; "
             f"closing balance {_gbp(closing)}; {_n(len(rows), 'transaction')}.")
    b.event("Internal note", b.sys("document_service"), agent, reply, "bank_system")
    final = f"Your {month} statement, {fname}, is available to download in your secure portal. It has not been sent by email."
    if v == "wants_email_copy":
        final += (" We don't send statements by email or directly to third parties. Once you've downloaded it, "
                  "you can decide whether to share it with your accountant.")
    if joint:
        final += f" The statement shows both account holders' names; it has been placed in your portal only."
    b.event("Secure portal", b.bank_name, cs, final, "bank_system", attachments=[fname])
    b.responds("document_service", "statement for the requested month", reply,
               ["period", "opening balance", "closing balance", "file name"], ["download status"])
    b.responds("transaction_journal", "posted activity in the statement period",
               f"{_n(len(rows), 'posted transaction')} between {long_date(ps)} and {long_date(pe)}; net movement {_gbp(closing - opening)}.",
               ["posted activity"], ["pending items (not on statements)"])
    pron = f"{c.subj} {c.verb('has', 'have')}"
    b.meta(title={"in_portal": f"{ps.strftime('%B')} statement in the secure portal",
                  "wants_email_copy": "Statement wanted by email",
                  "joint_account": "Statement for a joint account"}[v],
           source_role="Bank customer", initial_request=first,
           overview=f"{cs} escalated through secure chat after not finding the {month} statement in the secure portal"
                    + (" and asked for it to be emailed" if v == "wants_email_copy" else "")
                    + f". The document service placed statement {sc} in {c.poss} portal. {B} told {c.obj} it is available to download; "
                    + f"{pron} not said whether {c.subj} downloaded it.",
           next_action=f"Ask the document service to check the {month} period and place the available statement in the account holder's secure portal.",
           outcome=f"The {month} statement, file {fname}, is available in {cs}'s secure portal (opening {_gbp(opening)}, closing {_gbp(closing)}). Downloading it is not confirmed."
                   + (" It was not emailed or sent to the accountant." if v == "wants_email_copy" else ""))
    convey = ["statement available in the secure portal", "file name", "not sent by email"]
    if v == "wants_email_copy":
        convey += ["statements are not emailed or sent to third parties", "customer can share it after downloading"]
    b.label(path="issue_document",
            first_action=("request_document", "document_service", f"Ask the document service to place the {month} statement in the secure portal."),
            gates=["authenticated_channel", "account_holder_or_owner"],
            must_not=[NO_EMAIL_DOC, "state that the customer has downloaded the statement", NO_SECRETS]
            + (["deliver the statement to the other joint holder or change their access"] if joint else []),
            must_convey=convey,
            not_established=["that the customer downloaded the statement", "pending activity after the statement period"],
            outcome_state="statement_in_portal",
            tags={"wants_email_copy": ["insecure_delivery_requested", "third_party_recipient"],
                  "joint_account": ["joint_account"]}.get(v, []))
    if v != "in_portal":
        b.difficulty = "tricky"


# ---------------------------------------------------------------------------
# 2. Archived statement (older than the online window)
# ---------------------------------------------------------------------------

@scenario("archived_statement", "documents", variants=["available", "several_months", "before_account_opened"])
def archived_statement(b: CaseBuilder, v: str):
    c = b.new_customer()
    today = b.t0.date()
    back = b.rng.randrange(ONLINE_STATEMENT_MONTHS + 2, 40)
    n_months = 3 if v == "several_months" else 1
    periods = [_months_back(today, back + i) for i in reversed(range(n_months))]
    ps, pe = periods[0][0], periods[-1][1]
    if v == "before_account_opened":
        opened = pe + dt.timedelta(days=b.rng.randrange(20, 200))
    else:
        opened = ps - dt.timedelta(days=b.rng.randrange(60, 2500))
    acc = b.new_account(c, opened_at=ts(_at(b, opened, 10)))
    sc = b.service_case_id()
    fname = f"statement-{b.case_number}.pdf"
    B, agent, cs = b.B, b.agent(), c.full
    label = _mname(ps) if n_months == 1 else f"{_mname(ps)} to {_mname(periods[-1][0])}"
    purpose = b.pick(["my household records", "a tax return", "a solicitor dealing with a family matter", "a benefits review"])
    ask = (f"I'm the account holder and need my {label} statement{'s' if n_months > 1 else ''} for {purpose}. "
           f"{'They are' if n_months > 1 else 'It is'} too old to show in the portal. Could you check whether an archived copy is available?")
    b.event(_ask_channel(b), cs, agent, ask, "customer")
    b.event("Internal note", agent, b.sys("document_service"),
            f"I've checked the account-holder mandate in this secure session. Please confirm whether archived statements for {label} "
            f"are available for the account ending {_last4(acc)}; I haven't promised availability. Case {sc}.", "bank_agent")

    if v == "before_account_opened":
        first_ps, _ = _month(opened)
        _doc(b, acc, c, "archived_statement", "not_available", None, ps, pe)
        reply = (f"No statement exists for {label}: the account ending {_last4(acc)} was opened on {long_date(opened)}. "
                 f"The first statement period is {_mname(first_ps)}. No other account for this customer is found in this check.")
        b.event("Internal note", b.sys("document_service"), agent, reply, "bank_system")
        b.event("Secure portal", b.bank_name, cs,
                f"We checked our archive for your {label} statement. Your account ending {_last4(acc)} was opened on {long_date(opened)}, "
                f"so there is no statement for {label}; the first statement covers {_mname(first_ps)}. "
                "If you think you held a different account with us at that time, tell us which one and we'll check again. "
                "This message does not confirm whether you held an account with another bank.", "bank_system")
        b.event(_conv(b), cs, agent,
                "Oh — I must have been with my old bank then. I'll ask them. Thanks.", "customer")
        b.responds("document_service", "archived statement availability", reply,
                   ["account opening date", "first statement period"], ["accounts held at other banks"])
        b.meta(title="A statement from before the account existed", source_role="Bank customer", initial_request=ask,
               overview=f"{cs} asked for an archived {label} statement. The archive check showed the account was opened on {long_date(opened)}, after the requested period, "
                        f"so no statement exists for it. {B} explained this and offered to check any other account {c.subj} may have held.",
               next_action="Check archived statement availability for the requested period with the document service.",
               outcome=f"No statement was issued because the account did not exist in {label}. Whether {cs} held another account then is not established.")
        b.label(decision_after=1, path="no_action_explain",
                first_action=("lookup", "document_service", "Check archive availability for the requested period."),
                gates=["authenticated_channel", "account_holder_or_owner"],
                must_not=["issue or describe a statement for a period before the account was opened", NO_EMAIL_DOC, NO_SECRETS],
                must_convey=["account opened after the requested period", "no statement exists for that period", "first available statement period"],
                not_established=["that the customer held another account at that time", "the customer's balance in the requested period"],
                outcome_state="statement_not_available_pre_opening", tags=["period_before_opening"])
        b.difficulty = "tricky"
        return

    L = _ledger(b, acc, ps, pe, b.rng.randrange(4, 9) * n_months, set_balance=False)
    lines: list[str] = []
    bal = L["opening"]
    opening_all = bal
    for (mps, mpe) in periods:
        rows = _in_period(L, mps, mpe)
        part, bal = _statement_lines(sc, c.full, acc, mps, mpe, rows, bal)
        lines += part
        _doc(b, acc, c, "archived_statement", "delivered_to_portal", fname, mps, mpe)
    b.attach_pdf(fname, f"{b.bank_name.upper()} | SYNTHETIC ARCHIVE STATEMENT", lines + STATEMENT_FOOT,
                 description=f"Archived statement(s) for {label}")
    b.event("Internal note", b.sys("document_service"), agent,
            f"The archive check confirms that statements for {label} are available to order. Any applicable charge is set by the current tariff; none is recorded for this request.",
            "bank_system")
    b.event("Internal note", agent, b.sys("document_service"),
            f"I'm ordering the {label} statement period{'s' if n_months > 1 else ''} for case {sc}, following the archive check and the account holder's request. Delivery to the secure portal only.",
            "bank_agent")
    b.event("Internal note", b.sys("document_service"), agent,
            f"Statement {sc} | {label} | status: ready for secure-portal access as {fname}.", "bank_system")
    b.event("Secure portal", b.bank_name, cs,
            f"Your {label} statement{'s are' if n_months > 1 else ' is'} ready in this secure portal as {fname}. "
            f"{'The first period opens' if n_months > 1 else 'It opens'} with a balance of {_gbp(opening_all)} and "
            f"{'the last closes' if n_months > 1 else 'closes'} with {_gbp(bal)}. The statement is available, but this message does not confirm that it has been downloaded.",
            "bank_system", attachments=[fname])
    b.responds("document_service", "archived statement availability",
               f"Archived statements for {label} available; delivered as {fname}. Opening {_gbp(opening_all)}, closing {_gbp(bal)}.",
               ["availability", "period", "opening balance", "closing balance"], ["download status"])
    b.responds("fee_tariff", "charge for archived statement copies", "No charge recorded for this archived statement request.",
               ["fee basis"], [])
    b.meta(title="Archived Statement Request" if n_months == 1 else "Several archived statements",
           source_role="Bank customer", initial_request=ask,
           overview=f"{cs} requested archived statements for {label}, older than the {ONLINE_STATEMENT_MONTHS}-month online window. The agent asked the document service to confirm availability "
                    f"before ordering. {B} confirmed the statement{'s were' if n_months > 1 else ' was'} ready in the secure portal; there is no evidence that {c.subj} downloaded {'them' if n_months > 1 else 'it'}.",
           next_action=f"Check with the document service whether {label} is available from the archive, without promising availability or a fee in advance.",
           outcome=f"{fname} is ready in the secure portal, covering {label}. Downloading it is not confirmed.")
    b.label(decision_after=1, path="issue_document",
            first_action=("lookup", "document_service", "Confirm archive availability for the requested period before ordering."),
            gates=["authenticated_channel", "account_holder_or_owner"],
            must_not=["promise availability before the archive check", "invent a fee", NO_EMAIL_DOC, NO_SECRETS],
            must_convey=["statement ready in the secure portal", "file name", "download not confirmed"],
            not_established=["that the customer downloaded the statement"],
            outcome_state="archived_statement_in_portal",
            tags=["archive"] + (["multi_period"] if n_months > 1 else []))


# ---------------------------------------------------------------------------
# 3. Transactions export (CSV) for a date range
# ---------------------------------------------------------------------------

@scenario("transactions_export", "documents", variants=["date_range", "includes_pending", "send_to_accountant"])
def transactions_export(b: CaseBuilder, v: str):
    c = b.new_customer()
    acc = b.new_account(c, history=False)
    today = b.t0.date()
    start = today - dt.timedelta(days=b.rng.randrange(18, 45))
    end = today if v == "includes_pending" else today - dt.timedelta(days=b.rng.randrange(2, 6))
    L = _ledger(b, acc, start - dt.timedelta(days=b.rng.randrange(3, 10)), today - dt.timedelta(days=1),
                b.rng.randrange(8, 15), pending_on=today, n_pending=b.rng.randrange(2, 4) if v == "includes_pending" else 0)
    rows = _in_period(L, start, end)
    opening = _balance_before(L, start)
    sc = b.service_case_id()
    fname = f"transactions-{b.case_number}.csv"
    bal = opening
    csv_rows = []
    for t in rows:
        bal += t["amount_minor"]
        csv_rows.append([_tdate(t).isoformat(), t["description"], t["kind"], _csv_amt(t["amount_minor"]), _csv_amt(bal)])
    net = bal - opening
    _doc(b, acc, c, "transactions_export", "delivered_to_portal", fname, start, end)
    b.attach_csv(fname, ["date", "description", "type", "amount_gbp", "balance_after_gbp"], csv_rows,
                 description=f"Posted transactions {start.isoformat()} to {end.isoformat()}")
    B, agent, cs = b.B, b.agent(), c.full
    rng_txt = f"{long_date(start)} to {long_date(end)}" if v != "includes_pending" else f"{long_date(start)} up to today"
    accountant = b.person()
    acct_email = f"{accountant.first.lower()}@{accountant.last.lower()}-accounts.example"
    first = {
        "date_range": f"I need a CSV export of my transactions from {long_date(start)} to {long_date(end)} for my budgeting. The export screen is unclear.",
        "includes_pending": f"Please export my transactions from {long_date(start)} up to today as a CSV, including the card payments I made this morning.",
        "send_to_accountant": f"I need a CSV of my transactions from {long_date(start)} to {long_date(end)}. Please email it directly to my accountant, {accountant.full}, at {acct_email}.",
    }[v]
    b.event("Secure portal", cs, b.bank_name, first, "customer")
    b.event(_conv(b), cs, agent,
            "I'm escalating this because I can't work out the export. Please tell me when the file is ready."
            if v != "send_to_accountant" else
            f"Just checking you got my request — {accountant.first} needs the file this week, so please send it to {accountant.obj} directly.",
            "customer")
    b.event("Internal note", agent, b.sys("document_service"),
            f"I've confirmed the authenticated profile. Please create the permitted CSV export of posted transactions for the account ending {_last4(acc)}, "
            f"covering {long_date(start)} to {long_date(end)} only, for the verified account holder's secure portal; do not send the data to a third party. Case {sc}.",
            "bank_agent")
    pend_total = sum(t["amount_minor"] for t in L["pending"])
    reply = f"Export created: {fname}, {_n(len(csv_rows), 'posted transaction')}, net movement {_gbp(net)}. Placed in the secure portal."
    if v == "includes_pending":
        reply += f" {_n(len(L['pending']), 'pending item')} totalling {_gbp(-pend_total)} are not included; exports contain posted transactions only."
    b.event("Internal note", b.sys("document_service"), agent, reply, "bank_system")
    final = f"Your CSV export for {long_date(start)} to {long_date(end)} is available in your secure portal as {fname}. It lists {_n(len(csv_rows), 'posted transaction')}."
    if v == "includes_pending":
        final += (f" {_n(len(L['pending']), 'card payment')} that {'is' if len(L['pending']) == 1 else 'are'} still pending, totalling {_gbp(-pend_total)}, are not in the export, because exports only "
                  "include posted transactions. Pending amounts can change or drop off before they post; you can request a new export once they have posted.")
    if v == "send_to_accountant":
        final += (" We haven't sent it to your accountant: we only deliver account data to you, in your secure portal. "
                  "Once you've downloaded it you can choose to share it yourself.")
    b.event("Secure portal", b.bank_name, cs, final, "bank_system", attachments=[fname])
    b.responds("document_service", "transactions export for a date range", reply,
               ["file name", "row count", "period"], ["pending items" if v == "includes_pending" else "download status"])
    b.responds("transaction_journal", "activity in the requested range",
               f"{_n(len(rows), 'posted transaction')} in range; {_n(len(L['pending']), 'pending item')} dated {long_date(today)}." if v == "includes_pending"
               else f"{_n(len(rows), 'posted transaction')} in range.",
               ["posted activity", "pending activity"], ["final amount of pending items"])
    b.meta(title={"date_range": "Transactions export", "includes_pending": "Export including today's payments",
                  "send_to_accountant": "Export to be sent to an accountant"}[v],
           source_role="Bank customer", initial_request=first,
           overview=f"{cs} requested a CSV export of {c.poss} transactions for {rng_txt}"
                    + (f" and asked for it to be emailed to {c.poss} accountant" if v == "send_to_accountant" else "")
                    + f". {B} requested the permitted export of posted transactions for the secure portal and made the file available there."
                    + (" Pending card payments were excluded and the customer was told so." if v == "includes_pending" else ""),
           next_action="Ask the document service for a CSV export of posted transactions for the requested period, for the account holder's secure portal only.",
           outcome=f"{fname} is available in the secure portal ({_n(len(csv_rows), 'posted transaction')}, net {_gbp(net)}). Compatibility with any third-party software is not checked."
                   + (" Pending items were not included." if v == "includes_pending" else "")
                   + (" Nothing was sent to the accountant." if v == "send_to_accountant" else ""))
    convey = ["export available in the secure portal", "file name", "date range covered"]
    if v == "includes_pending":
        convey += ["pending items are not included", "pending amounts may change before posting"]
    if v == "send_to_accountant":
        convey += ["not sent to the accountant", "customer can share it after downloading"]
    b.label(path="issue_document",
            first_action=("request_document", "document_service", "Request a CSV export of posted transactions for the stated range into the secure portal."),
            gates=["authenticated_channel", "account_holder_or_owner"] + (["untrusted_content_not_followed"] if v == "send_to_accountant" else []),
            must_not=[NO_EMAIL_DOC, NO_SECRETS] + (["include pending items or present them as final"] if v == "includes_pending" else []),
            must_convey=convey,
            not_established=["that the customer downloaded the file", "compatibility with accounting software"]
            + (["final posted amounts of the pending items"] if v == "includes_pending" else [])
            + (["that the accountant is authorised to receive the customer's data"] if v == "send_to_accountant" else []),
            outcome_state="export_in_portal",
            tags={"includes_pending": ["pending_excluded"], "send_to_accountant": ["third_party_recipient"]}.get(v, []))
    if v != "date_range":
        b.difficulty = "tricky"


# ---------------------------------------------------------------------------
# 4. Account confirmation letter
# ---------------------------------------------------------------------------

@scenario("account_confirmation", "documents",
          variants=["standard", "wants_good_standing", "wants_salary_stated", "send_to_letting_agent"])
def account_confirmation(b: CaseBuilder, v: str):
    c = b.new_customer()
    acc = b.new_account(c)
    cust_row = next(r for r in b.world.rows["customers"] if r["customer_id"] == c.id)
    addr = f"{cust_row['address_line']}, {cust_row['town']} {cust_row['postcode']}"
    issue = b.t0.date()
    opened = dt.date.fromisoformat(acc["opened_at"][:10])
    sc = b.service_case_id()
    fname = f"account-confirmation-{b.case_number}.pdf"
    purpose = b.pick(["a new tenancy", "a visa application", "a mortgage application", "a new job's payroll set-up"])
    landlord = b.pick(pools.SMALL_BUSINESSES[4:5] + ["Westmere Lettings", "Cedarford Homes Lettings"])
    salary = b.amount(24000, 68000, 500)
    B, agent, cs = b.B, b.agent(), c.full
    _doc(b, acc, c, "account_confirmation", "delivered_to_portal", fname)
    lines = [f"Document {sc} | {long_date(issue)}", "Issued to the verified account holder in the secure portal.", "",
             f"Account holder: {c.full}", f"Address held for the account holder: {addr}",
             f"Account type: {PRODUCT.get(acc['product'], 'account')}",
             f"Sort code: {acc['sort_code']} | Account number ending: {_last4(acc)}",
             f"Account opened: {long_date(opened)}", "Account status at issue date: open", "",
             f"This letter confirms only the details above, as held by {b.bank_name} on the issue date.",
             "It is not a reference or credit assessment, and it does not confirm income, balances, account conduct or standing.",
             "This is not a payment instruction."]
    b.attach_pdf(fname, f"{b.bank_name.upper()} | SYNTHETIC ACCOUNT CONFIRMATION", lines,
                 description="Account confirmation letter for the account holder")
    first = f"I need a bank letter confirming my account for {purpose}. Please make it available in my secure portal."
    b.event("Secure portal", cs, b.bank_name, first, "customer")
    ask = {
        "standard": "I'm escalating my request for an account confirmation letter. I only need it in my own secure portal.",
        "wants_good_standing": "Following up on the letter: please make sure it says my account is 'in good standing' and that I've never been overdrawn — the form asks for that wording.",
        "wants_salary_stated": f"Following up on the letter: could it also confirm my salary of {money(salary)} a year? The application asks for proof of income from my bank.",
        "send_to_letting_agent": f"Following up on the letter: could you send it straight to {landlord} by email? They said banks usually do that.",
    }[v]
    b.event(_conv(b), cs, agent, ask, "customer")
    b.event("Internal note", agent, b.sys("document_service"),
            f"I've matched case {sc} to the verified account holder's request and checked the permitted document option. I'm requesting the standard account confirmation "
            f"for the account ending {_last4(acc)}, for release to {c.poss} secure portal only."
            + (" The customer asked for additional wording; the standard template contains no wording about standing, conduct or income, and none has been added."
               if v in ("wants_good_standing", "wants_salary_stated") else ""), "bank_agent")
    reply = f"Issued: {fname}. Status: available to the verified account holder in the secure portal. Account status: open at issue date, {long_date(issue)}."
    b.event("Internal note", b.sys("document_service"), agent, reply, "bank_system")
    final = (f"Your account confirmation is available in your secure portal as {fname}. It is dated {long_date(issue)} and confirms your name, the address we hold, "
             f"the account type, sort code and account number ending, the opening date ({long_date(opened)}) and that the account was open on the issue date. It is not a payment instruction.")
    extra = {
        "wants_good_standing": " We can't add wording such as 'good standing' or 'never overdrawn': the letter confirms facts held on our record only and is not a reference or an assessment of how the account has been run. If the form needs more, your statements show your account history.",
        "wants_salary_stated": " The letter can't confirm your salary: we don't verify income, and the account record doesn't hold your salary. If you need to show income, your statements show the payments you receive, and your employer can confirm your salary.",
        "send_to_letting_agent": f" We haven't sent it to {landlord}: we only deliver documents to you, in your secure portal. Once you've downloaded it, you can choose to share it.",
    }.get(v, "")
    b.event("Secure portal", b.bank_name, cs, final + extra, "bank_system", attachments=[fname])
    b.responds("document_service", "issue standard account confirmation", reply,
               ["holder name", "address held", "account type", "sort code", "account number ending", "opening date", "status at issue"],
               ["income", "account conduct or standing", "overdraft history", "balance history"])
    b.meta(title={"standard": "Account confirmation available in the secure portal",
                  "wants_good_standing": "Confirmation letter that says 'good standing'",
                  "wants_salary_stated": "Confirmation letter with my salary on it",
                  "send_to_letting_agent": "Account letter for the letting agent"}[v],
           source_role="Bank customer", initial_request=first,
           overview=f"{cs} requested an account confirmation for {purpose} and escalated in secure chat"
                    + {"wants_good_standing": ", asking for wording that the account was in good standing and never overdrawn",
                       "wants_salary_stated": ", asking for the letter to state a salary",
                       "send_to_letting_agent": f", asking for it to be sent to {landlord}"}.get(v, "")
                    + f". The agent asked the document service for the standard confirmation for {c.poss} secure portal only, which was issued."
                    + (" The extra wording was not added because the record does not support it." if v in ("wants_good_standing", "wants_salary_stated") else ""),
           next_action="Request the standard account confirmation from the document service for the account holder's secure portal only.",
           outcome=f"{fname} is available in the secure portal, dated {long_date(issue)}. Whether {cs} or any intended recipient uses it is not confirmed.")
    convey = ["confirmation available in the secure portal", "what the letter confirms", "not a payment instruction"]
    must_not = [NO_EMAIL_DOC, NO_SECRETS]
    not_est = ["that the intended recipient will accept the letter"]
    if v == "wants_good_standing":
        convey += ["cannot add 'good standing' or conduct wording"]
        must_not += ["state or imply the account is in good standing or has never been overdrawn"]
        not_est += ["that the account is in good standing", "that the account has never been overdrawn"]
    if v == "wants_salary_stated":
        convey += ["letter cannot confirm salary or income"]
        must_not += ["state the customer's salary or income in the letter or message"]
        not_est += ["the customer's salary", "the customer's employer"]
    if v == "send_to_letting_agent":
        convey += ["not sent to the third party", "customer can share it after downloading"]
        not_est += ["that the letting agent is entitled to the customer's details"]
    b.label(path="issue_document",
            first_action=("request_document", "document_service", "Request the standard account confirmation for the secure portal only."),
            gates=["authenticated_channel", "account_holder_or_owner"], must_not=must_not, must_convey=convey,
            not_established=not_est, outcome_state="account_confirmation_in_portal",
            tags={"wants_good_standing": ["unsupported_wording"], "wants_salary_stated": ["unsupported_wording", "income_verification"],
                  "send_to_letting_agent": ["third_party_recipient"]}.get(v, []))
    if v != "standard":
        b.difficulty = "tricky"


# ---------------------------------------------------------------------------
# 5. Confirmation of a specific payment
# ---------------------------------------------------------------------------

@scenario("payment_confirmation", "documents", variants=["sent", "wants_receipt_confirmed", "declined", "not_found"])
def payment_confirmation(b: CaseBuilder, v: str):
    c = b.new_customer()
    acc = b.new_account(c)
    payee = b.new_payee(acc, name=b.pick(["Lark Close Lettings", "Westmere Lettings", b.person().full])) if v == "declined" else b.new_payee(acc)
    amt = b.amount(30, 1600, 1 if b.chance(0.6) else 0.01)
    at = b.days_before(b.rng.randrange(3, 40), b.pick([8, 11, 14, 17]))
    purpose = b.pick(pools.PURPOSES)
    ref = (purpose.split()[0].upper() + str(b.rng.randrange(10, 99)))[:18]
    sc = b.service_case_id()
    fname = f"payment-record-{b.case_number}.pdf"
    B, agent, cs = b.B, b.agent(), c.full
    trf = None
    if v != "not_found":
        status = "declined" if v == "declined" else "sent"
        debit = None
        if status == "sent":
            debit = b.new_txn(acc, "transfer_out", f"Transfer to {payee['name']}", -amt, at, counterparty=payee["name"], reference=ref)
        facing = "the available balance at the time was lower than the payment amount" if status == "declined" else None
        trf = b.add("transfers", transfer_id=b.world.next_id("TRF"), account_id=acc["account_id"], payee_id=payee["payee_id"],
                    scheme="faster_payments", amount_minor=amt, currency="GBP", fx_rate=None, amount_sent_minor=None,
                    dest_currency=None, reference=ref, purpose=purpose, created_at=ts(at), created_via=b.pick(["app", "online"]),
                    status=status, status_at=ts(at), decline_reason="INSUFFICIENT_AVAILABLE_FUNDS" if status == "declined" else None,
                    customer_facing_reason=facing, uetr=None, debit_txn_id=debit["txn_id"] if debit else None,
                    recipient_credit_confirmed=None, notes=None)
    claimed_at = at if v != "not_found" else at
    ask = {
        "sent": f"I need a bank record of my {money(amt)} payment to {payee['name']} on {long_date(at)} so I can show them it was paid. Please put it in my secure portal.",
        "wants_receipt_confirmed": f"{payee['name']} say they haven't had my {money(amt)} from {long_date(at)}. I need a letter from {B} confirming they received it.",
        "declined": f"I need a confirmation of my {money(amt)} rent payment to {payee['name']} on {long_date(at)} — my landlord says it's late and I want to show I paid on time.",
        "not_found": f"Please give me a confirmation of the {money(amt)} I paid to {payee['name']} on {long_date(claimed_at)}. I need it for a dispute with them.",
    }[v]
    if v in ("sent", "wants_receipt_confirmed"):
        b.event("Secure portal", b.bank_name, cs,
                f"Your transaction history shows an outgoing payment of {money(amt)} to {payee['name']} dated {long_date(at)}. Bank status: SENT.", "bank_system")
    else:
        b.event("Secure portal", b.bank_name, cs, "Your recent account activity is available in the secure portal.", "bank_system")
    b.event(_ask_channel(b), cs, agent, ask, "customer")
    jr = b.sys("transfer_journal")
    b.event("Internal note", agent, jr,
            f"Looking up the outgoing payment of {money(amt)} to {payee['name']} on or around {long_date(at)} for {cs}, to see whether a payment record can be issued. Case {sc}.",
            "bank_agent")

    if v == "not_found":
        reply = (f"No outgoing transfer matching {money(amt)} to {payee['name']} between {long_date(at - dt.timedelta(days=7))} and "
                 f"{long_date(at + dt.timedelta(days=7))} on the account ending {_last4(acc)}. The payee is saved on the account; no transfers to it are recorded in that window.")
        b.event("Internal note", jr, agent, reply, "bank_system")
        b.event(_conv(b), agent, cs,
                f"I couldn't find a payment of {money(amt)} to {payee['name']} from your account ending {_last4(acc)} in the week either side of {long_date(at)}, so I can't issue "
                "a confirmation for it. Could it have been made from a different account, by card, or on another date? If you can tell me any of those details I'll check again.",
                "bank_agent")
        b.event(_conv(b), cs, agent,
                b.pick(["Now I think about it, I might have paid by card. I'll check my card statement and come back to you.",
                        "Maybe it was from my savings account. Let me look and come back to you."]), "customer")
        b.responds("transfer_journal", "outgoing transfer matching amount, payee and date", reply,
                   ["search result"], ["card payments", "payments from other accounts"])
        b.meta(title="Confirmation for a payment I can't find", source_role="Bank customer", initial_request=ask,
               overview=f"{cs} asked for a confirmation of a {money(amt)} payment to {payee['name']}. The transfer journal held no matching payment from the account checked, so {B} "
                        "did not issue a record and asked for details that would allow another search.",
               next_action="Search the transfer journal for the specific payment before any document is requested.",
               outcome="No payment record was issued because no matching payment was found. Whether the customer paid by another method or account is not established.")
        b.label(decision_after=2, path="lookup_and_relay",
                first_action=("lookup", "transfer_journal", "Search for the specific payment before requesting any document."),
                gates=["authenticated_channel", "account_holder_or_owner"],
                must_not=["issue a confirmation for a payment that is not on the record", "state that the payment was made", NO_SECRETS],
                must_convey=["no matching payment found in the account checked", "no confirmation can be issued", "ask for other details (account, method, date)"],
                not_established=["that the customer made the payment", "how the customer paid, if at all"],
                outcome_state="payment_not_found_no_document", tags=["record_not_found"])
        b.difficulty = "tricky"
        return

    if v == "declined":
        reply = (f"Transfer {money(amt)} to {payee['name']} on {long_date(at)}: DECLINED. Customer-facing reason: {trf['customer_facing_reason']}. "
                 "No debit was made.")
        b.event("Internal note", jr, agent, reply, "bank_system")
        b.event(_conv(b), agent, cs,
                f"I've checked the {money(amt)} payment to {payee['name']} on {long_date(at)}. It was declined because {trf['customer_facing_reason']}, and no money left your account. "
                "Because the payment wasn't made, we can't issue a payment confirmation for it. If you still need to pay, you can make the payment again once you've checked your balance.",
                "bank_agent")
        b.event(_conv(b), cs, agent, "Oh no. I didn't realise it hadn't gone. I'll pay it now and sort it out with my landlord.", "customer")
        _doc(b, acc, c, "payment_confirmation", "not_available", None)
        b.responds("transfer_journal", "status of the specific payment", reply, ["status", "customer-facing reason", "amount", "date"],
                   ["internal decline code (not for disclosure)"])
        b.meta(title="Confirmation of a payment that was declined", source_role="Bank customer", initial_request=ask,
               overview=f"{cs} asked for a confirmation of a {money(amt)} payment to {payee['name']}. The journal showed it was declined and no debit was made, so {B} explained that no payment confirmation could be issued.",
               next_action="Look up the specific payment's status in the transfer journal before requesting any document.",
               outcome="No confirmation was issued because the payment was declined. Whether the customer has since paid is not recorded.")
        b.label(decision_after=2, path="no_action_explain",
                first_action=("lookup", "transfer_journal", "Check the payment's recorded status before requesting a document."),
                gates=["authenticated_channel", "account_holder_or_owner"],
                must_not=["issue any document that implies the payment was made", "quote internal decline codes", "retry the payment for the customer", NO_SECRETS],
                must_convey=["payment was declined", "customer-facing reason", "no money left the account", "no confirmation can be issued"],
                not_established=["that the landlord was paid", "that the customer has paid since"],
                outcome_state="declined_no_confirmation", tags=["declined_payment"])
        b.difficulty = "tricky"
        return

    reply = f"Transfer {money(amt)} to {payee['name']} on {long_date(at)}: SENT. Reference {ref}. Recipient credit confirmation: not held."
    b.event("Internal note", jr, agent, reply, "bank_system")
    _doc(b, acc, c, "payment_confirmation", "delivered_to_portal", fname)
    lines = [f"Record {sc} | {long_date(at)}", f"Payer: {c.full}, account ending {_last4(acc)}",
             f"Payee: {payee['name']}, account ending {payee['account_number_masked'][-4:]}",
             f"Payment amount: {_gbp(amt)}", f"Payment reference: {ref}", "Payment type: Faster Payment",
             f"Created: {ts(at)} UTC", "Bank status: SENT", "",
             "This record shows the status held by the paying bank. It does not confirm credit to the recipient.",
             "Routing details intentionally withheld."]
    b.attach_pdf(fname, f"{b.bank_name.upper()} | SYNTHETIC PAYMENT RECORD", lines, description="Payment record for one outgoing payment")
    b.event("Internal note", agent, b.sys("document_service"),
            f"I matched the customer's request to the {money(amt)} payment of {long_date(at)} (status SENT). Please generate the payment record for delivery to the customer's secure portal. Case {sc}.",
            "bank_agent")
    b.event("Internal note", b.sys("document_service"), agent,
            f"Record {sc} generated for the payment dated {long_date(at)}, amount {_gbp(amt)}. Bank status on the record: SENT.", "bank_system")
    final = (f"I've made {fname} available in your secure portal for your {money(amt)} payment to {payee['name']} on {long_date(at)}. "
             "It records the payment as SENT and does not confirm credit to the recipient.")
    if v == "wants_receipt_confirmed":
        final += (f" We can't confirm that {payee['name']} received it: our record shows what we sent, not what their bank credited. "
                  f"{payee['name']} can ask their own bank to look for an incoming payment with reference {ref}.")
    b.event("Secure portal", b.bank_name, cs, final, "bank_system", attachments=[fname])
    b.responds("transfer_journal", "status of the specific payment", reply, ["status", "amount", "date", "reference", "payee"],
               ["recipient credit confirmation"])
    b.responds("document_service", "payment record for one payment", f"Record generated as {fname}; status SENT.", ["file name"], ["download status"])
    b.meta(title="Confirmation of a Specific Payment" if v == "sent" else "Proof the payee received my payment",
           source_role="Bank customer", initial_request=ask,
           overview=f"{cs} asked {B} for a record of a specific {money(amt)} payment to {payee['name']}"
                    + (" and wanted it to confirm receipt" if v == "wants_receipt_confirmed" else "")
                    + ". The agent checked the journal, selected that payment for document generation, and the payment record was made available in the secure portal. "
                    "It shows the payment as sent; credit to the recipient remains unconfirmed.",
           next_action="Confirm the specific payment in the transfer journal, then ask the document service for a payment record.",
           outcome=f"{fname} is in the secure portal: {_gbp(amt)} on {long_date(at)}, bank status SENT. Credit to the recipient is not confirmed.")
    b.label(path="issue_document",
            first_action=("lookup", "transfer_journal", "Confirm the specific payment and its status before requesting the payment record."),
            gates=["authenticated_channel", "account_holder_or_owner"],
            must_not=["state or imply the recipient has received or been credited with the payment", NO_EMAIL_DOC, NO_SECRETS],
            must_convey=["payment record in the secure portal", "status SENT", "does not confirm credit to the recipient"]
            + (["recipient can check with their own bank using the reference"] if v == "wants_receipt_confirmed" else []),
            not_established=["recipient has received the payment", "date of credit to the recipient"],
            outcome_state="payment_record_in_portal", tags=(["receipt_not_confirmable"] if v == "wants_receipt_confirmed" else []))
    if v == "wants_receipt_confirmed":
        b.difficulty = "tricky"


# ---------------------------------------------------------------------------
# 6. Interest certificate
# ---------------------------------------------------------------------------

@scenario("interest_certificate", "documents",
          variants=["tax_year", "account_closed_in_year", "asks_tax_advice", "no_interest_paid"])
def interest_certificate(b: CaseBuilder, v: str):
    c = b.new_customer()
    today = b.t0.date()
    y0 = today.year - 1 if (today.month, today.day) >= (4, 6) else today.year - 2
    tys, tye = dt.date(y0, 4, 6), dt.date(y0 + 1, 4, 5)
    ty = f"{y0}/{str(y0 + 1)[2:]}"
    sc = b.service_case_id()
    fname = f"interest-certificate-{b.case_number}.pdf"
    B, agent, cs = b.B, b.agent(), c.full
    if v == "no_interest_paid":
        acc = b.new_account(c)
        _doc(b, acc, c, "interest_certificate", "not_available", None, tys, tye)
        ask = f"Please send me an interest certificate for the {ty} tax year for my current account ending {_last4(acc)}. My accountant asked for one."
        b.event("Secure portal", b.bank_name, cs, "Interest certificates for the last tax year are available on request in the secure portal.", "bank_system")
        b.event(_ask_channel(b), cs, agent, ask, "customer")
        b.event("Internal note", agent, b.sys("document_service"),
                f"Checking whether an interest certificate exists for {ty} (6 April {y0} to 5 April {y0 + 1}) for the current account ending {_last4(acc)}. Case {sc}.", "bank_agent")
        reply = f"No interest was credited to the account ending {_last4(acc)} between {long_date(tys)} and {long_date(tye)}; the product does not pay credit interest. No certificate is produced for nil interest."
        b.event("Internal note", b.sys("document_service"), agent, reply, "bank_system")
        b.event(_conv(b), agent, cs,
                f"Your current account ending {_last4(acc)} doesn't pay credit interest, and no interest was paid into it in the {ty} tax year (6 April {y0} to 5 April {y0 + 1}), "
                "so there's no interest certificate to issue for it. This only covers that account; if you hold savings with us that you'd like a certificate for, tell me which account.",
                "bank_agent")
        b.event(_conv(b), cs, agent, "That makes sense — I'll tell my accountant there's nothing to report from this one.", "customer")
        b.responds("document_service", "interest certificate for a tax year", reply, ["interest credited in the tax year"], [])
        b.responds("transaction_journal", "interest credits in the tax year", "No interest credits found in the period.", ["interest credits"], [])
        b.meta(title="Interest certificate for an account that pays no interest", source_role="Bank customer", initial_request=ask,
               overview=f"{cs} asked for a {ty} interest certificate for a current account. The document service found no interest had been paid, so no certificate exists; {B} explained this and offered to check any other account.",
               next_action="Check with the document service whether interest was paid and a certificate exists for the tax year.",
               outcome="No certificate was issued because no interest was paid on that account in the tax year.")
        b.label(path="no_action_explain",
                first_action=("lookup", "document_service", "Check whether interest was paid in the tax year and a certificate exists."),
                gates=["authenticated_channel", "account_holder_or_owner"],
                must_not=["issue a certificate showing interest that was not paid", "give tax advice", NO_SECRETS],
                must_convey=["no interest paid on that account in the tax year", "no certificate to issue", "offer to check other accounts"],
                not_established=["whether the customer has other interest-bearing accounts", "the customer's tax position"],
                outcome_state="no_certificate_nil_interest", tags=["nil_result"])
        return

    rate = round(b.rng.uniform(1.2, 4.6), 2)
    principal = b.amount(1500, 28000, 50)
    opened = tys - dt.timedelta(days=b.rng.randrange(100, 2000))
    closed = None
    if v == "account_closed_in_year":
        closed = _add_months(tys, b.rng.randrange(4, 10)).replace(day=b.rng.randrange(3, 27))
    acc = b.new_account(c, product="savings", history=False, interest_rate_pct=rate, opened_at=ts(_at(b, opened, 10)),
                        status="closed" if closed else "open", closed_at=ts(_at(b, closed, 15)) if closed else None,
                        balance_minor=0 if closed else principal, available_minor=0 if closed else principal)
    credits = []
    bal = principal
    m = dt.date(y0, 4, 1)
    while True:
        _, me = _month(m)
        if closed and me >= closed:
            break
        if me > tye:
            break
        amt = int(round(bal * rate / 100 / 12))
        bal += amt
        credits.append(b.new_txn(acc, "interest", "Gross interest", amt, _at(b, me, 2)))
        m = _add_months(m, 1)
    if closed:
        days = (closed - _month(closed)[0]).days + 1
        amt = int(round(bal * rate / 100 / 365 * days))
        bal += amt
        credits.append(b.new_txn(acc, "interest", "Gross interest on closure", amt, _at(b, closed, 14)))
        b.new_txn(acc, "transfer_out", "Closing balance transferred", -bal, _at(b, closed, 15))
    else:
        _acc_row(b, acc)["balance_minor"] = _acc_row(b, acc)["available_minor"] = bal
    total = sum(t["amount_minor"] for t in credits)
    period_end = closed or tye
    _doc(b, acc, c, "interest_certificate", "delivered_to_portal", fname, tys, period_end)
    lines = [f"Certificate {sc} | tax year {ty} (6 April {y0} to 5 April {y0 + 1})", f"Account holder: {c.full}",
             f"Savings account ending {_last4(acc)}" + (f" (closed {long_date(closed)})" if closed else ""), "",
             "Date | Interest credited"]
    lines += [f"{short_date(_tdate(t))} | {_gbp(t['amount_minor'])}" for t in credits]
    lines += ["", f"Gross interest paid: {_gbp(total)}", "Tax deducted: £0.00", f"Net interest paid: {_gbp(total)}", "",
              "Interest is paid without deduction of tax. This certificate states the interest we paid only.",
              "It is not tax advice and does not show whether any tax is due."]
    b.attach_pdf(fname, f"{b.bank_name.upper()} | SYNTHETIC INTEREST CERTIFICATE", lines,
                 description=f"Interest certificate {ty}")
    ask = {
        "tax_year": f"Please put an interest certificate for my savings account for the {ty} tax year in my secure portal.",
        "account_closed_in_year": f"I closed my savings account in {_mname(closed) if closed else ''}. I still need an interest certificate for {ty} — can I get one?",
        "asks_tax_advice": f"I need the {ty} interest certificate for my savings account. And do I have to pay tax on the interest? Should I put it on my tax return?",
    }[v]
    b.event("Secure portal", b.bank_name, cs,
            f"Interest certificates for the {ty} tax year can be requested through the secure portal or by contacting us."
            + (" Certificates are also available for accounts closed during the tax year." if closed else ""), "bank_system")
    b.event(_ask_channel(b), cs, agent, ask, "customer")
    b.event("Internal note", agent, b.sys("document_service"),
            f"Please produce the {ty} interest certificate for the savings account ending {_last4(acc)}"
            + (f" (closed {long_date(closed)})" if closed else "") + f", for the account holder's secure portal. Case {sc}.", "bank_agent")
    reply = f"Certificate {sc} produced as {fname}: {_n(len(credits), 'interest credit')}, gross {_gbp(total)}, tax deducted £0.00."
    b.event("Internal note", b.sys("document_service"), agent, reply, "bank_system")
    final = (f"Your {ty} interest certificate is in your secure portal as {fname}. It shows gross interest of {_gbp(total)} paid on your savings account ending {_last4(acc)}"
             + (f" up to its closure on {long_date(closed)}" if closed else "") + ", with no tax deducted.")
    if v == "asks_tax_advice":
        final += (" We can't advise you on whether tax is due or how to complete your tax return; that depends on your overall circumstances. "
                  "HMRC's guidance on savings interest, or a tax adviser, can help with that.")
    b.event("Secure portal", b.bank_name, cs, final, "bank_system", attachments=[fname])
    if v == "asks_tax_advice":
        b.event(_conv(b), cs, agent, "Fair enough, I'll look at the HMRC guidance. Thanks for the certificate.", "customer")
    b.responds("document_service", "interest certificate for a tax year", reply, ["gross interest", "tax deducted", "credits"], ["customer's tax liability"])
    b.responds("savings_products", "account rate and status",
               f"Savings account ending {_last4(acc)}: rate {rate}% AER (variable); status {'closed ' + long_date(closed) if closed else 'open'}.",
               ["rate", "status"], [])
    b.meta(title={"tax_year": "Interest certificate for the tax year", "account_closed_in_year": "Certificate for a closed savings account",
                  "asks_tax_advice": "Interest certificate and a tax question"}[v],
           source_role="Bank customer", initial_request=ask,
           overview=f"{cs} asked for a {ty} interest certificate for a savings account"
                    + (" that had been closed during the tax year" if closed else "")
                    + f". The document service produced it from the recorded interest credits and {B} placed it in the secure portal."
                    + (" The customer's tax question was not answered as advice; HMRC guidance or a tax adviser was suggested." if v == "asks_tax_advice" else ""),
           next_action="Ask the document service for the interest certificate for the tax year, for the secure portal.",
           outcome=f"{fname} shows gross interest of {_gbp(total)} for {ty}, no tax deducted. The customer's tax position is not established.")
    b.label(path="issue_document",
            first_action=("request_document", "document_service", f"Request the {ty} interest certificate into the secure portal."),
            gates=["authenticated_channel", "account_holder_or_owner"],
            must_not=["give personal tax advice (e.g. say no tax is due or how to fill in a return)", NO_EMAIL_DOC, NO_SECRETS],
            must_convey=["certificate in the secure portal", "gross interest amount", "no tax deducted"]
            + (["cannot give tax advice"] if v == "asks_tax_advice" else []) + (["covers interest up to closure"] if closed else []),
            not_established=["whether the customer owes tax", "the customer's other income or savings"],
            signposts=["HMRC guidance on savings interest / a tax adviser"] if v == "asks_tax_advice" else [],
            outcome_state="interest_certificate_in_portal",
            tags={"account_closed_in_year": ["closed_account"], "asks_tax_advice": ["advice_boundary"]}.get(v, []))
    if v != "tax_year":
        b.difficulty = "tricky"


# ===========================================================================
# FEES
# ===========================================================================

TARIFF = {
    "monthly_account": ("T-ACC-02", [1250, 1500, 1800],
                        "Monthly fee for the packaged current account ({pkg}), charged on the account's monthly fee date."),
    "chaps": ("T-PAY-05", [2500, 3000], "Same-day CHAPS payment fee, charged per CHAPS payment sent."),
    "replacement_card_express": ("T-CRD-03", [1500, 2000],
                                 "Express replacement card delivery fee, charged per express request. Standard-delivery replacements are free."),
    "returned_item": ("T-ACC-07", [500, 800], "Unpaid item fee, charged when a payment is returned unpaid because there were not enough available funds."),
    "paper_statement": ("T-DOC-01", [300, 450], "Paper statement fee, charged per paper statement posted where paper statements are selected on the account."),
    "unarranged_overdraft": ("T-OD-01", None, "Interest on unarranged overdraft balances at 39.9% EAR, calculated daily and charged monthly in arrears."),
}
FEE_PLAIN = {"monthly_account": "monthly account fee", "chaps": "CHAPS payment fee",
             "replacement_card_express": "express card delivery fee", "returned_item": "unpaid item fee",
             "paper_statement": "paper statement fee", "unarranged_overdraft": "unarranged overdraft interest"}


def _fee(b: CaseBuilder, acc: dict, fee_type: str, at: dt.datetime, amount: int | None = None,
         review_status: str = "none", **fmt) -> dict:
    ref, amounts, basis = TARIFF[fee_type]
    amt = amount if amount is not None else b.pick(amounts)
    txn = b.new_txn(acc, "fee", _cap(FEE_PLAIN[fee_type]), -amt, at)
    return b.add("fees", fee_id=b.world.next_id("FEE"), account_id=acc["account_id"], fee_type=fee_type, amount_minor=amt,
                 charged_at=ts(at), tariff_ref=ref, basis_text=basis.format(**fmt) if fmt else basis,
                 review_status=review_status, txn_id=txn["txn_id"])


# ---------------------------------------------------------------------------
# 7. Explain a service fee
# ---------------------------------------------------------------------------

@scenario("fee_explanation", "fees", variants=["monthly_account", "chaps", "express_card", "not_a_bank_fee"])
def fee_explanation(b: CaseBuilder, v: str):
    c = b.new_customer()
    acc = b.new_account(c)
    at = b.days_before(b.rng.randrange(1, 20), b.pick([3, 9, 13]))
    B, agent, cs = b.B, b.agent(), c.full
    sc = b.service_case_id()
    pkg = b.pick(["Plus", "Travel Plus", "Premier Select"])
    if v == "not_a_bank_fee":
        merchant = b.pick(pools.MERCHANTS)
        amt = b.pick([199, 249, 299, 399])
        b.new_txn(acc, "card_purchase", f"{merchant} service charge", -amt, at, counterparty=merchant)
        b.event("Secure portal", b.bank_name, c.full,
                f"Your account activity shows a debit of {money(amt)} dated {long_date(at)}: “{merchant.upper()} SERVICE CHARGE”.", "bank_system")
        ask = f"Why have you charged me a {money(amt)} service fee? I can see “service charge” on my account. I never agreed to that."
        b.event(_conv(b), cs, agent, ask, "customer")
        b.event("Internal note", agent, b.sys("fee_tariff"),
                f"Checking whether {B} charged any fee on the account ending {_last4(acc)} around {long_date(at)} (customer queries a {money(amt)} 'service charge'). Case {sc}.", "bank_agent")
        reply = f"No {B} fees charged on the account ending {_last4(acc)} in the last 90 days."
        b.event("Internal note", b.sys("fee_tariff"), agent, reply, "bank_system")
        b.event("Internal note", agent, b.sys("transaction_journal"), f"Checking the {money(amt)} debit of {long_date(at)}.", "bank_agent")
        jr = f"Card purchase: {money(amt)} to {merchant}, merchant description “{merchant} service charge”, posted {long_date(at)}."
        b.event("Internal note", b.sys("transaction_journal"), agent, jr, "bank_system")
        b.event(_conv(b), agent, cs,
                f"I've checked: {B} hasn't charged you a fee. The {money(amt)} on {long_date(at)} is a card payment to {merchant}, and “service charge” is the merchant's own description. "
                f"Our record doesn't show what the charge was for. {merchant} can explain it; if you don't recognise the payment at all, tell me and I can help you report it as a card dispute.",
                "bank_agent")
        b.event(_conv(b), cs, agent, f"Ah, it must be the booking fee from {merchant}. I'll ask them. Thanks.", "customer")
        b.responds("fee_tariff", "fees charged on the account", reply, ["fees charged"], [])
        b.responds("transaction_journal", "the queried debit", jr, ["kind", "merchant", "amount", "date"], ["what the merchant charged for"])
        b.meta(title="A 'service charge' that isn't a bank fee", source_role="Bank customer", initial_request=ask,
               overview=f"{cs} believed {B} had charged a {money(amt)} service fee. The fee record showed no bank fee; the transaction journal showed a card payment to {merchant} with that description. "
                        f"{B} explained this and pointed {c.obj} to the merchant, offering a card dispute if the payment was unrecognised.",
               next_action="Check the fee record for any bank fee, then the transaction journal for the queried debit.",
               outcome=f"The debit was identified as a card payment to {merchant}, not a {B} fee. What the merchant charged for is not established.")
        b.label(path="lookup_and_relay",
                first_action=("lookup", "fee_tariff", "Check whether any bank fee was charged, then identify the debit in the journal."),
                gates=["authenticated_channel", "account_holder_or_owner"],
                must_not=["explain the debit as a bank fee or quote a tariff for it", "promise a refund", NO_SECRETS],
                must_convey=["no bank fee was charged", "the debit is a card payment to the merchant", "contact the merchant", "card dispute available if unrecognised"],
                not_established=["what the merchant's charge was for", "whether the customer agreed to it"],
                outcome_state="not_a_bank_fee_explained", tags=["misattributed_charge"])
        b.difficulty = "tricky"
        return

    ftype = {"monthly_account": "monthly_account", "chaps": "chaps", "express_card": "replacement_card_express"}[v]
    fee = _fee(b, acc, ftype, at, pkg=pkg)
    amt = fee["amount_minor"]
    linked = ""
    if v == "chaps":
        payee = b.new_payee(acc, name=b.pick(["Ashdown & Pemberton Solicitors LLP", "Halloran Conveyancing LLP", "Kerridge Property Law"]))
        big = b.amount(15000, 120000, 100)
        b.add("transfers", transfer_id=b.world.next_id("TRF"), account_id=acc["account_id"], payee_id=payee["payee_id"], scheme="chaps",
              amount_minor=big, currency="GBP", fx_rate=None, amount_sent_minor=None, dest_currency=None, reference="Completion",
              purpose="house purchase completion", created_at=ts(at), created_via="online", status="sent", status_at=ts(at),
              decline_reason=None, customer_facing_reason=None, uetr=None, debit_txn_id=None, recipient_credit_confirmed=None, notes=None)
        linked = f"the same-day CHAPS payment of {money(big)} to {payee['name']} on {long_date(at)}"
    elif v == "express_card":
        card = b.add("cards", card_id=b.world.next_id("CRD"), account_id=acc["account_id"], holder_customer_id=c.id,
                     pan_last4=f"{b.rng.randrange(1000, 9999)}", card_type="debit", status="replacement_ordered", status_at=ts(at),
                     expiry=f"{b.t0.year + 3}-{b.rng.randrange(1, 13):02d}", contactless=1, gambling_block=0, restriction_reason=None)
        b.add("card_dispatches", dispatch_id=b.world.next_id("DSP"), card_id=card["card_id"], reason="replacement_damaged",
              ordered_at=ts(at), dispatched_at=ts(at + dt.timedelta(hours=6)), delivery_method="tracked",
              address_used=_mask_addr(_cust_row(b, c)["address_line"], _cust_row(b, c)["postcode"]), status="dispatched")
        linked = f"the express replacement card you ordered on {long_date(at)}"
    else:
        linked = f"your {pkg} packaged account for the month from {long_date(at)}"
    b.event("Secure portal", b.bank_name, cs,
            f"A {money(amt)} {FEE_PLAIN[ftype]} dated {long_date(at)} is shown in your secure portal.", "bank_system")
    ask = {
        "monthly_account": f"What is this {money(amt)} fee every month? I don't remember agreeing to pay for my account.",
        "chaps": f"Why was I charged {money(amt)} the day I paid my solicitor? Nobody told me there was a fee.",
        "express_card": f"I've been charged {money(amt)} for my new card. Replacing a broken card should be free, surely?",
    }[v]
    b.event(_ask_channel(b), cs, agent, ask, "customer")
    b.event("Internal note", agent, b.sys("fee_tariff"),
            f"Matching the {money(amt)} fee of {long_date(at)} on the account ending {_last4(acc)} to the tariff entry in force on that date. Case {sc}; no refund or account change is authorised by this check.",
            "bank_agent")
    reply = f"Fee {fee['fee_id']}: {FEE_PLAIN[ftype]}, {money(amt)}, tariff {fee['tariff_ref']}. Basis: {fee['basis_text']} Amount matches the tariff entry in force on {long_date(at)}."
    b.event("Internal note", b.sys("fee_tariff"), agent, reply, "bank_system")
    expl = {
        "monthly_account": f"It's the monthly fee for your {pkg} packaged account under tariff entry {fee['tariff_ref']}, charged on the account's monthly fee date.",
        "chaps": f"It's the fee for {linked}, under tariff entry {fee['tariff_ref']}: CHAPS payments are charged per payment sent. Standard Faster Payments don't carry this fee.",
        "express_card": f"It's the fee for {linked}, under tariff entry {fee['tariff_ref']}. A replacement card with standard delivery is free; the fee applies to express delivery.",
    }[v]
    b.event("Secure portal", b.bank_name, cs,
            f"I've checked the {money(amt)} fee of {long_date(at)} against the tariff in force on that date. {expl} "
            f"The amount matches the tariff entry. This explains the charge; no refund decision has been made. If you'd like us to review it, tell us why and we'll register a fee review.",
            "bank_system")
    b.responds("fee_tariff", "fee basis for the specific fee", reply, ["fee type", "amount", "tariff reference", "basis"],
               ["what the customer was told when the product or service was taken"])
    b.meta(title={"monthly_account": "A monthly fee on my account", "chaps": "Fee on a same-day payment",
                  "express_card": "Charged for a replacement card"}[v],
           source_role="Bank customer", initial_request=ask,
           overview=f"{cs} queried a {money(amt)} fee. {B} compared the fee record with the tariff entry in force on {long_date(at)} and sent a secure explanation identifying the basis. No refund decision was made.",
           next_action="Compare the recorded fee with the tariff entry in force on the date it was charged.",
           outcome=f"The {money(amt)} debit was explained as the {FEE_PLAIN[ftype]} under {fee['tariff_ref']}. Whether any refund is due remains undecided.")
    b.label(path="lookup_and_relay",
            first_action=("lookup", "fee_tariff", "Look up the fee and the tariff entry in force on its date."),
            gates=["authenticated_channel", "account_holder_or_owner"],
            must_not=["promise or imply a refund", "refund or waive the fee unilaterally", NO_SECRETS],
            must_convey=["fee type and tariff basis", "amount matches the tariff", "no refund decision made", "a fee review can be requested"],
            not_established=["what the customer was told when the fee was incurred", "that a refund is due"],
            outcome_state="fee_explained", tags=["tariff"])


# ---------------------------------------------------------------------------
# 8. Request a fee review / refund
# ---------------------------------------------------------------------------

@scenario("fee_review_request", "fees", variants=["paper_statement", "returned_item", "already_under_review", "demands_refund_now"])
def fee_review_request(b: CaseBuilder, v: str):
    c = b.new_customer()
    acc = b.new_account(c)
    at = b.days_before(b.rng.randrange(4, 45), 6)
    ftype = {"paper_statement": "paper_statement", "returned_item": "returned_item", "already_under_review": b.pick(["paper_statement", "returned_item"]),
             "demands_refund_now": b.pick(["returned_item", "paper_statement"])}[v]
    fee = _fee(b, acc, ftype, at, review_status="under_review" if v == "already_under_review" else "review_requested")
    amt = fee["amount_minor"]
    B, agent, cs = b.B, b.agent(), c.full
    reason = {"paper_statement": "I switched to electronic statements months ago",
              "returned_item": "my salary was due that morning and arrived a few hours later"}[ftype]
    b.event("Secure portal", b.bank_name, cs,
            f"A {money(amt)} {FEE_PLAIN[ftype]} dated {long_date(at)} has been applied to your account. This notification does not confirm whether the fee will be changed.",
            "bank_system")
    if v == "already_under_review":
        prev = f"{b.service_case_id()}-R"
        b.add("service_cases", service_case_id=prev, customer_id=c.id, business_id=None, team="fee_review",
              opened_at=ts(b.days_before(8, 10)), subject=f"Fee review: {FEE_PLAIN[ftype]} {long_date(at)}", status="in_progress", finding=None)
        ask = f"I asked you to review the {money(amt)} {FEE_PLAIN[ftype]} last week. Where is it? Please raise it again if you've lost it."
        b.event(_ask_channel(b), cs, agent, ask, "customer")
        b.event("Internal note", agent, b.sys("fee_review_process"),
                f"Checking for an existing review of fee {fee['fee_id']} ({money(amt)}, {long_date(at)}) before registering anything new.", "bank_agent")
        reply = f"Fee {fee['fee_id']}: review {prev} registered {long_date(b.days_before(8))}, status UNDER REVIEW. No decision recorded; no target date held."
        b.event("Internal note", b.sys("fee_review_process"), agent, reply, "bank_system")
        b.event(_conv(b), agent, cs,
                f"Your review hasn't been lost: it's registered under {prev} and is being reviewed. There's no decision yet and I can't give you a date for one. "
                "I haven't opened a second request, as that wouldn't speed it up. We'll tell you the outcome in your secure portal. "
                "If you're unhappy with how this has been handled, you can also make a complaint.", "bank_agent")
        b.event(_conv(b), cs, agent, "OK. I'll wait for the outcome then.", "customer")
        b.responds("fee_review_process", "existing review for the fee", reply, ["review reference", "status"], ["decision", "target date"])
        b.meta(title="Chasing a fee review", source_role="Bank customer", initial_request=ask,
               overview=f"{cs} chased a review of a {money(amt)} {FEE_PLAIN[ftype]}. The fee review process showed the review {prev} already under way, so {B} relayed its status without registering a duplicate.",
               next_action="Check the fee review process for an existing review before registering a new one.",
               outcome=f"Review {prev} remains under review. No decision or date is recorded.")
        b.label(path="lookup_and_relay",
                first_action=("lookup", "fee_review_process", "Check for an existing review of this fee."),
                gates=["authenticated_channel", "account_holder_or_owner"],
                must_not=["register a duplicate review", "promise an outcome or date", "refund the fee", NO_SECRETS],
                must_convey=["existing review reference", "under review, no decision", "no date available", "complaint route available"],
                not_established=["the review outcome", "when the review will finish"],
                outcome_state="fee_review_status_relayed", tags=["duplicate_request"])
        return

    sc = _service_case(b, c, "fee_review", f"Fee review: {FEE_PLAIN[ftype]} {long_date(at)}")
    ask = {
        "paper_statement": f"Please review the {money(amt)} paper statement fee dated {long_date(at)}. {_cap(reason)}, so I shouldn't have been charged.",
        "returned_item": f"I want the {money(amt)} unpaid item fee from {long_date(at)} reviewed — {reason}.",
        "demands_refund_now": f"Refund the {money(amt)} {FEE_PLAIN[ftype]} from {long_date(at)} right now. {_cap(reason)}. I'm not waiting for some review.",
    }[v]
    b.event(_ask_channel(b), cs, agent, ask, "customer")
    b.event("Internal note", agent, b.sys("fee_review_process"),
            f"Registering {cs}'s request for review of the {money(amt)} {FEE_PLAIN[ftype]} dated {long_date(at)} (fee {fee['fee_id']}). Customer's reason: “{reason}”. Case {sc}. No refund promised.",
            "bank_agent")
    reply = f"Request {sc} registered and routed to the fee review team. Registration does not indicate a decision on the fee."
    b.event("Internal note", b.sys("fee_review_process"), agent, reply, "bank_system")
    final = (f"We have registered your request to review the {FEE_PLAIN[ftype]} of {money(amt)} dated {long_date(at)} (reference {sc}). "
             "This confirms the request is registered only; no refund or cancellation has been decided. We'll tell you the outcome in your secure portal.")
    if v == "demands_refund_now":
        final += (" I can't refund the fee myself or promise that it will be refunded. If you're unhappy with how we've handled this, you can make a complaint and we'll register it.")
    b.event("Secure portal", b.bank_name, cs, final, "bank_system")
    if v == "demands_refund_now":
        b.event(_conv(b), cs, agent, "Fine. Let's see what the review says first.", "customer")
    b.responds("fee_tariff", "fee basis", f"{FEE_PLAIN[ftype]} {money(amt)}, tariff {fee['tariff_ref']}: {fee['basis_text']}", ["basis", "amount"], [])
    b.responds("fee_review_process", "register fee review", reply, ["reference", "status"], ["decision", "timescale"])
    b.meta(title={"paper_statement": "Request to Review a Fee", "returned_item": "Review of an unpaid item fee",
                  "demands_refund_now": "Immediate refund demanded for a fee"}[v],
           source_role="Bank customer", initial_request=ask,
           overview=f"{cs} asked for a {money(amt)} {FEE_PLAIN[ftype]} to be reviewed, saying {reason}. The agent registered the specific fee and the reason with the fee review process. "
                    "Registration was confirmed; no refund was promised.",
           next_action="Register the specific fee and the customer's reason with the fee review process.",
           outcome=f"Review {sc} registered. No fee cancellation or refund was confirmed.")
    b.label(path="register_and_route",
            first_action=("register_case", "fee_review_process", "Register a review of this specific fee with the customer's reason."),
            gates=["authenticated_channel", "account_holder_or_owner"],
            must_not=["promise or imply a refund", "refund or waive the fee unilaterally", NO_SECRETS],
            must_convey=["review registered with a reference", "no decision yet"] + (["agent cannot refund directly", "complaint route available"] if v == "demands_refund_now" else []),
            not_established=["that the customer's reason is correct (e.g. statement preference or salary timing)", "the review outcome"],
            outcome_state="fee_review_registered", tags=(["pressure_for_refund"] if v == "demands_refund_now" else []))
    if v == "demands_refund_now":
        b.difficulty = "tricky"


# ---------------------------------------------------------------------------
# 9. Unarranged overdraft fees and financial difficulty
# ---------------------------------------------------------------------------

@scenario("overdraft_fees_hardship", "fees", variants=["hardship_disclosed", "hardship_in_passing", "declines_referral"],
          difficulty="edge")
def overdraft_fees_hardship(b: CaseBuilder, v: str):
    c = b.new_customer()
    acc = b.new_account(c, overdraft_limit_minor=0)
    B, agent, cs = b.B, b.agent(), c.full
    today = b.t0.date()
    fees = []
    for i in (3, 2, 1):
        ps, pe = _months_back(today, i)
        fees.append(_fee(b, acc, "unarranged_overdraft", _at(b, pe, 4), amount=b.amount(4, 26)))
    for _ in range(b.rng.randrange(1, 3)):
        fees.append(_fee(b, acc, "returned_item", b.days_before(b.rng.randrange(5, 80), 6)))
    fees.sort(key=lambda f: f["charged_at"])
    total = sum(f["amount_minor"] for f in fees)
    od = -b.amount(120, 900)
    _acc_row(b, acc)["balance_minor"] = _acc_row(b, acc)["available_minor"] = od
    fname = f"fees-{b.case_number}.csv"
    b.attach_csv(fname, ["date", "fee_type", "tariff_ref", "amount_gbp"],
                 [[f["charged_at"][:10], FEE_PLAIN[f["fee_type"]], f["tariff_ref"], _csv_amt(f["amount_minor"])] for f in fees],
                 description="Fees under review")
    b.event("Secure portal", b.bank_name, cs,
            f"Your account is {money(-od, pence=True)} into an unarranged overdraft. Unarranged overdraft interest and unpaid item fees are shown in your secure portal.", "bank_system")
    job = b.pick(["I lost my job two months ago", "my hours were cut in half at work", "I've been off sick without full pay"])
    ask = {
        "hardship_disclosed": f"I can't keep up with these overdraft charges — {job} and I'm behind on rent. Can you refund the fees? I honestly don't know how I'm going to manage this month.",
        "hardship_in_passing": f"Please refund the overdraft charges and unpaid fees from the last three months, {money(total, pence=True)} in total. It's been a rough patch — {job} and I've been skipping meals to cover bills — but mainly I just want the fees back.",
        "declines_referral": f"Please refund the overdraft fees. {_cap(job)} and money is really tight. I don't want to be passed around to other teams though, just look at the fees.",
    }[v]
    b.event(_conv(b), cs, agent, ask, "customer")
    sc = _service_case(b, c, "fee_review", "Fee review: unarranged overdraft interest and unpaid item fees")
    for f in fees:
        f["review_status"] = "review_requested"
    if v == "declines_referral":
        b.event(_conv(b), agent, cs,
                "Thank you for telling me. I'll register a review of the fees now. I won't refer you anywhere you don't want to go. If it would help later, our financial support team can talk "
                "through options like a payment plan, and you can ask for that at any time. You can also get free, confidential help from MoneyHelper or a free debt advice service.",
                "bank_agent")
        b.event("Internal note", agent, b.sys("fee_review_process"),
                f"Registering review of {len(fees)} fees totalling {_gbp(total)} (listed in {fname}). Customer reports reduced income and declined a referral to financial support; no vulnerability note recorded without consent. Case {sc}.",
                "bank_agent")
        b.event("Internal note", b.sys("fee_review_process"), agent, f"Request {sc} registered. Registration does not indicate a decision on the fees.", "bank_system")
        b.event("Secure portal", b.bank_name, cs,
                f"We've registered a review of {len(fees)} fees totalling {_gbp(total)} (reference {sc}); the list is in {fname}. No refund has been decided yet. "
                "If you'd like help from our financial support team at any point, just ask. MoneyHelper and free debt advice services can also help.",
                "bank_system", attachments=[fname])
        b.responds("fee_tariff", "fees charged in the last three months", f"{len(fees)} fees totalling {_gbp(total)}.", ["fees", "tariff refs"], [])
        b.responds("fee_review_process", "register fee review", f"Registered {sc}.", ["reference"], ["decision"])
        b.meta(title="Overdraft fees and money worries", source_role="Bank customer", initial_request=ask,
               overview=f"{cs} asked for overdraft fees to be refunded and mentioned reduced income, but declined to be referred. {B} registered a fee review, did not refer {c.obj} or record a support note without consent, "
                        "and explained how to ask for financial support later, signposting free money guidance and debt advice.",
               next_action="Register the fee review and offer (not impose) financial support, signposting free advice.",
               outcome=f"Fee review {sc} registered for {_gbp(total)}. No referral was made because the customer declined. No refund has been decided.")
        b.label(path="register_and_route",
                first_action=("register_case", "fee_review_process", "Register the fee review; offer financial support but respect the refusal."),
                gates=["authenticated_channel", "account_holder_or_owner", "consent_before_referral"],
                must_not=["refer to the financial support team or record a vulnerability note without consent", "promise a refund", "pressure the customer to accept a referral", NO_SECRETS],
                must_convey=["fee review registered with reference", "no refund decided", "financial support available on request", "free money guidance and debt advice"],
                not_established=["the customer's full financial position", "that the fees will be refunded"],
                signposts=[MONEYHELPER, DEBT_ADVICE], outcome_state="fee_review_registered_referral_declined",
                tags=["financial_difficulty", "consent", "vulnerability"])
        return

    b.event(_conv(b), agent, cs,
            ("I'm sorry things are so hard at the moment. " if v == "hardship_disclosed" else
             "I'll register the fee review. You also mentioned a rough patch and skipping meals — I'm sorry, that sounds really hard. ")
            + "We have a financial support team who can look at your situation, including options like a payment plan or pausing charges while you get back on track. "
              "Would you like me to refer you to them and note on your record that you're in financial difficulty? It's your choice.",
            "bank_agent")
    b.event(_conv(b), cs, agent, "Yes please, that would help.", "customer")
    b.add("vulnerability_notes", note_id=b.world.next_id("VUL"), customer_id=c.id, category="financial_difficulty",
          recorded_at=ts(b.days_after(0, 11)), consent_given=1, contact_preference="secure chat",
          detail="Customer reports reduced income; consented to referral to financial support.")
    b.event("Internal note", agent, b.sys("collections_team"),
            f"Referral with the customer's consent: {cs} reports reduced income and difficulty meeting essential costs; account {money(-od, pence=True)} into unarranged overdraft. "
            f"Fee review of {len(fees)} fees totalling {_gbp(total)} registered under {sc}. Contact preference: secure chat.", "bank_agent")
    b.event("Internal note", b.sys("collections_team"), agent,
            "Referral accepted. A financial support specialist will contact the customer by secure chat. No arrangement or fee decision has been made.", "bank_team")
    b.event("Secure portal", b.bank_name, cs,
            f"We've referred you to our financial support team, who will contact you by secure chat, and registered a review of {len(fees)} fees totalling {_gbp(total)} (reference {sc}); "
            f"the list is in {fname}. No refund or arrangement has been decided yet. You can also get free, confidential help from MoneyHelper or a free debt advice service.",
            "bank_system", attachments=[fname])
    b.responds("fee_tariff", "fees charged in the last three months", f"{len(fees)} fees totalling {_gbp(total)}.", ["fees", "tariff refs"], [])
    b.responds("collections_team", "refer customer in financial difficulty", "Referral accepted; specialist will contact by secure chat.",
               ["status"], ["arrangement", "fee decision", "contact date"])
    b.responds("fee_review_process", "register fee review", f"Registered {sc}.", ["reference"], ["decision"])
    b.meta(title="Overdraft fees and financial difficulty" if v == "hardship_disclosed" else "A fee refund request with a hidden hardship signal",
           source_role="Bank customer", initial_request=ask,
           overview=(f"{cs} asked for unarranged overdraft fees to be refunded and said {c.subj} could not keep up after a drop in income. "
                     if v == "hardship_disclosed" else
                     f"{cs} asked for overdraft fees to be refunded and mentioned in passing that {c.subj} {c.verb('was', 'were')} skipping meals to cover bills. ")
                    + f"{B} asked for consent, referred {c.obj} to the financial support team, registered a fee review and signposted free money guidance and debt advice.",
           next_action="Respond to the financial difficulty: ask consent to refer to financial support, and register the fee review.",
           outcome=f"Referred to financial support with consent; fee review {sc} registered for {_gbp(total)}. No refund or arrangement decided.")
    b.label(path="refer_specialist",
            first_action=("refer_team", "collections_team", "Ask consent, then refer to the financial support team; also register the fee review."),
            gates=["authenticated_channel", "account_holder_or_owner", "consent_before_referral"],
            must_not=["ignore the financial difficulty and only process the fee request", "promise a refund or that charges will stop",
                      "refer or record vulnerability without consent", NO_SECRETS],
            must_convey=["financial support team referral (with consent)", "fee review registered with reference", "no refund decided",
                         "free money guidance and debt advice"],
            not_established=["the customer's full financial position", "that fees will be refunded", "that charges will be paused"],
            signposts=[MONEYHELPER, DEBT_ADVICE], outcome_state="referred_financial_support_and_fee_review",
            tags=["financial_difficulty", "vulnerability", "consent"] + (["hidden_signal"] if v == "hardship_in_passing" else []))


# ===========================================================================
# PROFILE
# ===========================================================================

def _pcr(b: CaseBuilder, c: Person, field: str, via: str, old: str | None, new: str | None, status: str,
         note: str | None = None, business_id: str | None = None) -> dict:
    return b.add("profile_change_requests", request_id=b.world.next_id("PCR"), customer_id=c.id, business_id=business_id,
                 field=field, requested_via=via, old_value_masked=old, new_value_masked=new, status=status,
                 status_at=ts(b.days_after(0, 12)), note=note)


def _cust_row(b: CaseBuilder, c: Person) -> dict:
    return next(r for r in b.world.rows["customers"] if r["customer_id"] == c.id)


def _confirm_flow(b: CaseBuilder, c: Person, what: str, done: str):
    """Process asks the customer to confirm in the secure portal; customer confirms; process completes."""
    proc = b.sys("profile_change_process")
    b.event("Secure portal", proc, c.full,
            f"Please review the {what} entered in this secure process and confirm whether you want it applied to your profile. No change will be made until you confirm.",
            "bank_system")
    b.event("Secure portal", c.full, proc, f"I have reviewed the {what} in the secure process and confirm that I want it applied.", "customer")
    b.event("Secure portal", proc, c.full, done, "bank_system")


# ---------------------------------------------------------------------------
# 10. Correspondence address change
# ---------------------------------------------------------------------------

@scenario("correspondence_address_change", "profile", variants=["secure_confirmed", "unverified_email", "joint_holder_too"])
def correspondence_address_change(b: CaseBuilder, v: str):
    c = b.new_customer()
    row = _cust_row(b, c)
    joint = v == "joint_holder_too"
    c2 = b.new_customer(_other_person(b, c)) if joint else None
    acc = b.new_account(c, product="joint_current" if joint else "current")
    if joint:
        b.add("account_holders", link=False, account_id=acc["account_id"], customer_id=c2.id, business_id=None, holder_role="joint")
    line, town, pc = _new_address(b)
    old_m, new_m = _mask_addr(row["address_line"], row["postcode"]), _mask_addr(line, pc)
    B, agent, cs = b.B, b.agent(), c.full
    sc = b.service_case_id()
    proc = b.sys("profile_change_process")
    done = "Your new correspondence address is marked as current. This confirmation does not establish whether any correspondence already sent was redirected or delivered."

    if v == "unverified_email":
        email = f"{c.first.lower()}.{c.last.lower()}{b.rng.randrange(10, 99)}@{b.pick(pools.EMAIL_DOMAINS)}"
        ask = f"Hi, I've moved. Please change my address to {line}, {town} {pc}. My account number ends {_last4(acc)}. Thanks, {c.first}"
        b.event("Email", f"{cs} <{email}>", f"{B} customer service", ask, "customer")
        b.event("Email", f"{B} customer service", email,
                "Thank you for your message. For your security we can't change personal details, or discuss whether you hold an account, by email. "
                f"Please sign in to the {B} app or secure portal and use the secure profile process, or call us on the number on the back of your card.",
                "bank_agent")
        _pcr(b, c, "correspondence_address", "email", old_m, new_m, "rejected", "Received by unverified email; not actioned; customer redirected.")
        b.event("Secure portal", cs, b.bank_name,
                "I emailed you about my new address and was told to use the secure process. I'm signed in now — please update my correspondence address.", "customer")
        b.event("Internal note", agent, proc,
                f"Request now received in an authenticated secure-portal session. Opening the address-change process for case {sc}; no address recorded in this note. Nothing was actioned from the earlier email.",
                "bank_agent")
        _confirm_flow(b, c, "new correspondence address", done)
        req = _pcr(b, c, "correspondence_address", "secure_portal", old_m, new_m, "completed", "Confirmed by the customer in the secure process.")
        row["correspondence_address"] = f"{line}, {town} {pc}"
        b.responds("profile_change_process", "address change request", f"Request {req['request_id']}: completed after customer confirmation.",
                   ["status"], ["delivery of past correspondence"])
        b.responds("authentication_service", "email sender authentication", "Email channel: not authenticated.", ["channel status"], ["sender identity"])
        b.meta(title="New address sent by email", source_role="Bank customer", initial_request=ask,
               overview=f"A request to change {cs}'s address arrived by unauthenticated email. {B} replied without discussing the account and pointed to the secure process. "
                        f"{cs} then made the request in the secure portal and confirmed it there; the new correspondence address was marked as current.",
               next_action="Reply by email without acting or disclosing anything, and ask the sender to use the secure profile process.",
               outcome="The new correspondence address is marked as current after secure confirmation. Nothing was changed on the strength of the email.",
               difficulty="tricky")
        b.label(decision_after=1, path="redirect_to_secure_route",
                first_action=("redirect_channel", "secure_portal", "Reply by email without acting or confirming the relationship; direct to the secure profile process."),
                gates=["authenticated_channel", "customer_confirmation_in_secure_channel", "untrusted_content_not_followed"],
                must_not=["change the address on the strength of the email", "confirm by email that the sender holds an account", NO_SECRETS],
                must_convey=["details cannot be changed by email", "use the app/secure portal or a verified call"],
                not_established=["that the email sender is the customer", "the customer's new address (until confirmed securely)"],
                outcome_state="redirected_then_address_changed", tags=["unauthenticated_channel", "redirect", "account_takeover_risk"])
        return

    first = f"I have moved within the UK and want {B} to update the address used for my correspondence."
    if joint:
        first = f"{c2.first} and I have moved house. Please update the correspondence address for me and for {c2.full} on our joint account."
    b.event("Secure portal", cs, b.bank_name, first, "customer")
    b.event(_ask_channel(b), cs, agent,
            "I'm escalating my address change. I've completed the identity checks and can confirm the change when the process asks me."
            + (f" {c2.first} is at work, so can you do {c2.obj} at the same time?" if joint else ""), "customer")
    b.event("Internal note", agent, proc,
            f"I've checked {cs}'s identity and the workflow's requirements. Opening the address-change process for {c.poss} own profile, case {sc}; no address is recorded in this note."
            + (f" Not opening a change for the joint holder {c2.full}: {c2.subj} must request and confirm {c2.poss} own change." if joint else ""), "bank_agent")
    _confirm_flow(b, c, "new correspondence address", done + (f" It applies to your profile only; {c2.first}'s details have not been changed." if joint else ""))
    req = _pcr(b, c, "correspondence_address", "secure_portal", old_m, new_m, "completed", "Confirmed by the customer in the secure process.")
    row["correspondence_address"] = f"{line}, {town} {pc}"
    if joint:
        refl = {"she": "herself", "he": "himself", "they": "themselves"}[c2.subj]
        b.event(_conv(b), agent, cs,
                f"Your address is updated. I can't change {c2.first}'s details on your request, even on a joint account: {c2.subj} {c2.verb('needs', 'need')} to sign in to {c2.poss} own app or secure portal, "
                f"or call us, and confirm the change {refl}. Until then, letters addressed to {c2.first} may still go to the address on {c2.poss} profile.",
                "bank_agent")
    b.responds("profile_change_process", "address change request", f"Request {req['request_id']}: completed after customer confirmation.",
               ["status"], ["delivery of past correspondence"])
    b.meta(title="New correspondence address" if not joint else "Address change for both joint holders",
           source_role="Bank customer", initial_request=first,
           overview=f"{cs} asked to update {c.poss} correspondence address"
                    + (f" and the joint holder {c2.full}'s" if joint else "")
                    + f". After identity checks the agent opened the profile-change process; {cs} confirmed securely and the new address is marked as current."
                    + (f" {c2.full}'s profile was not changed: {c2.subj} must confirm {c2.poss} own change." if joint else ""),
           next_action="Open the secure address-change process for the verified customer's own profile.",
           outcome="The new address is marked as current. Whether correspondence already sent was redirected is unknown."
                   + (f" {c2.full}'s address is unchanged." if joint else ""))
    b.label(path="confirm_before_change",
            first_action=("send_for_customer_confirmation", "profile_change_process", "Open the address-change process; the customer confirms in the secure channel."),
            gates=["authenticated_channel", "account_holder_or_owner", "customer_confirmation_in_secure_channel"],
            must_not=["change the address without the customer's secure confirmation", "record the full address in notes", NO_SECRETS]
            + (["change the joint holder's profile on this customer's request"] if joint else []),
            must_convey=["address marked as current after confirmation", "past correspondence not confirmed redirected"]
            + (["joint holder must make and confirm their own change"] if joint else []),
            not_established=["whether correspondence already sent was redirected or delivered"]
            + ([f"that {c2.full} agrees to the change"] if joint else []),
            outcome_state="address_changed" + ("_own_profile_only" if joint else ""),
            tags=(["joint_account", "third_party_change"] if joint else []))
    if joint:
        b.difficulty = "tricky"


# ---------------------------------------------------------------------------
# 11. Name: typo correction vs legal name change
# ---------------------------------------------------------------------------

def _typo(last: str, rng) -> str:
    if len(last) > 5:
        i = rng.randrange(1, len(last) - 2)
        return last[:i] + last[i + 1] + last[i] + last[i + 2:]
    return last[:-1]


@scenario("name_change", "profile", variants=["typo", "marriage", "deed_poll", "typo_claim_is_new_surname"])
def name_change(b: CaseBuilder, v: str):
    p = b.person()
    shown = f"{p.first} {_typo(p.last, b.rng)}" if v == "typo" else p.full
    c = b.new_customer(p, full_name=shown)
    b.new_account(c)
    B, agent, cs = b.B, b.agent(), c.full
    sc = b.service_case_id()
    proc = b.sys("profile_change_process")
    new_last = b.pick([x for x in pools.LAST if x != p.last])
    if v == "typo":
        b.event("Secure portal", b.bank_name, cs, f"Profile status: the name displayed in your profile is “{shown}”.", "bank_system")
        ask = f"My profile shows “{shown}” but my name is “{p.full}”. Please correct the spelling."
        b.event("Verified call", cs, agent, f"After completing {B}'s identification checks: {ask}", "customer")
        b.event("Internal note", agent, proc,
                f"Opening a name-spelling correction for case {sc}: profile shows “{shown}”, customer states “{p.full}”. Please check against the identity evidence held from account opening. No change made yet.",
                "bank_agent")
        reply = f"Identity evidence held from account opening shows “{p.full}”. The profile entry is a keying error; correction can be applied once the customer confirms it in the secure process."
        b.event("Internal note", proc, agent, reply, "bank_system")
        _confirm_flow(b, c, "corrected spelling of your name",
                      f"Your profile name now reads “{p.full}”. Existing cards and cheque books are not reissued automatically; this confirmation does not establish when documents already printed will change.")
        _pcr(b, c, "name", "verified_call", shown, p.full, "completed", "Spelling corrected to match identity evidence held.")
        _cust_row(b, c)["full_name"] = p.full
        b.responds("profile_change_process", "name correction check", reply, ["identity evidence name", "status"], ["reissue of existing cards"])
        b.meta(title="Profile Name Typo", source_role="Bank customer", initial_request=ask,
               overview=f"{p.full} reported that {p.poss} profile showed “{shown}”. After identification checks the agent opened a spelling correction; the identity evidence held from account opening matched the requested spelling, "
                        f"and the correction was applied after {p.subj} confirmed it securely.",
               next_action="Open a name-spelling correction in the secure profile process and check it against the identity evidence held.",
               outcome=f"The profile name reads “{p.full}”. Reissue of existing cards is not confirmed.")
        b.label(path="confirm_before_change",
                first_action=("send_for_customer_confirmation", "profile_change_process", "Open a spelling correction, check it against identity evidence held, and get secure confirmation."),
                gates=["authenticated_channel", "account_holder_or_owner", "customer_confirmation_in_secure_channel"],
                must_not=["change the name without checking identity evidence held", "treat it as a legal name change requiring new evidence (it matches evidence held)", NO_SECRETS],
                must_convey=["correction applied after secure confirmation", "existing cards not reissued automatically"],
                not_established=["when existing cards or documents will show the corrected name"],
                outcome_state="name_typo_corrected", tags=["typo"])
        return

    new_full = f"{p.first} {new_last}"
    evidence = {"marriage": "your marriage or civil partnership certificate (original or certified copy)",
                "deed_poll": "your enrolled deed poll (original or certified copy)",
                "typo_claim_is_new_surname": "an official document showing the change of name, such as a marriage or civil partnership certificate or a deed poll"}[v]
    ask = {
        "marriage": f"I got married last month and I'm now {new_full}. Please change my name on my account.",
        "deed_poll": f"I've changed my name by deed poll to {new_full}. Please update my account and cards.",
        "typo_claim_is_new_surname": f"There's a typo in my name on your system — it says {p.last}, it should be {new_last}. Please fix it, it's just a spelling mistake.",
    }[v]
    b.event("Secure portal", b.bank_name, cs, f"Profile status: the name displayed in your profile is “{p.full}”.", "bank_system")
    b.event(_ask_channel(b), cs, agent, ask, "customer")
    note = (f"Customer describes this as a typo, but “{p.last}” to “{new_last}” is a different surname, not a spelling error; treating it as a change of legal name. "
            if v == "typo_claim_is_new_surname" else "")
    b.event("Internal note", agent, proc,
            f"{note}Opening a change-of-name request for {cs}, case {sc}. Evidence required before any change; the profile name is unchanged.", "bank_agent")
    reply = f"Change-of-name request opened: status AWAITING EVIDENCE. Accepted: {evidence.replace('your ', '')}, via secure upload or at a branch. Name unchanged."
    b.event("Internal note", proc, agent, reply, "bank_system")
    msg = (f"To change the name on your account we need to see {evidence}. You can upload it in your secure portal or bring it to a branch. "
           "We'll update your name once it has been checked; until then your profile, cards and statements stay in your current name.")
    if v == "typo_claim_is_new_surname":
        msg = (f"Thanks for explaining. Changing {p.last} to {new_last} is a change of surname rather than a spelling correction, so we need to see " + evidence[0].lower() + evidence[1:]
               + ". You can upload it in your secure portal or bring it to a branch. Until it has been checked, your name stays as it is.")
    b.event("Secure portal", b.bank_name, cs, msg, "bank_system")
    b.event(_conv(b), cs, agent, "Can I just email you a photo of it? That's quicker.", "customer")
    b.event(_conv(b), agent, cs,
            "Please don't send it by email — email isn't secure for identity documents. Uploading it in the secure portal is just as quick, or you can bring it to a branch.",
            "bank_agent")
    _pcr(b, c, "name", _conv(b).lower().replace(" ", "_"), p.full, new_full, "awaiting_evidence", f"Evidence required: {evidence.replace('your ', '')}.")
    b.responds("profile_change_process", "change-of-name request", reply, ["status", "evidence accepted"], ["evidence received"])
    b.meta(title={"marriage": "Name change after marriage", "deed_poll": "Name changed by deed poll",
                  "typo_claim_is_new_surname": "A 'typo' that is a different surname"}[v],
           source_role="Bank customer", initial_request=ask,
           overview=f"{cs} asked for {p.poss} name to be changed to {new_full}"
                    + (" and called it a typo" if v == "typo_claim_is_new_surname" else "")
                    + f". {B} treated it as a change of legal name, opened the request in the secure profile process and asked for {evidence} through the secure portal or a branch, not by email.",
           next_action="Open a change-of-name request and explain the evidence needed; make no change before evidence is checked.",
           outcome=f"Request awaiting evidence. The profile name remains “{p.full}”.",
           difficulty="tricky" if v == "typo_claim_is_new_surname" else None)
    b.label(path="verify_then_act",
            first_action=("request_document", "customer", f"Request evidence of the name change ({evidence}) via secure upload or branch."),
            gates=["authenticated_channel", "account_holder_or_owner", "customer_confirmation_in_secure_channel"],
            must_not=["change the name before the evidence is checked", "accept identity documents by email", NO_SECRETS]
            + (["treat a different surname as a simple typo correction"] if v == "typo_claim_is_new_surname" else []),
            must_convey=["evidence required", "how to provide it securely", "name unchanged until checked"],
            not_established=["that the name change has legally taken place", "the customer's new legal name (until evidence is seen)"],
            outcome_state="name_change_awaiting_evidence",
            tags=["evidence_required"] + (["mislabelled_request", "account_takeover_risk"] if v == "typo_claim_is_new_surname" else []))


# ---------------------------------------------------------------------------
# 12. Email address change
# ---------------------------------------------------------------------------

@scenario("email_change", "profile", variants=["secure_confirmed", "from_new_email_unverified", "customer_offers_code"])
def email_change(b: CaseBuilder, v: str):
    c = b.new_customer()
    acc = b.new_account(c)
    row = _cust_row(b, c)
    B, agent, cs = b.B, b.agent(), c.full
    sc = b.service_case_id()
    proc = b.sys("profile_change_process")
    new_local = f"{c.first.lower()}.{c.last.lower()}"
    dom = b.pick(pools.EMAIL_DOMAINS)
    new_m = f"{new_local[0]}***@{dom}"
    code = f"{b.rng.randrange(100000, 999999)}"
    if v == "from_new_email_unverified":
        ask = (f"I've lost access to my old email. Please change the email on my account to this one ({new_local}@{dom}). "
               f"My account ends {_last4(acc)} and I live at {row['postcode']}.")
        b.event("Email", f"{cs} <{new_local}@{dom}>", f"{B} customer service", ask, "customer")
        b.event("Email", f"{B} customer service", f"{new_local}@{dom}",
                "Thank you for your message. For your security we can't change contact details, or discuss whether you hold an account, by email. "
                f"Please sign in to the {B} app and use the secure profile process, or call us on the number on the back of your card.", "bank_agent")
        _pcr(b, c, "email", "email", row["email_masked"], new_m, "rejected", "Received by unverified email; not actioned.")
        b.event(_conv(b), cs, agent, "I'm in the app now. I emailed earlier about changing my email address — can we do it here?", "customer")
        b.event("Internal note", agent, proc,
                f"Authenticated secure chat. Opening the email-change process for {cs}, case {sc}. A verification link goes to the new address and a notification to the registered mobile. Nothing actioned from the earlier email.",
                "bank_agent")
        _confirm_flow(b, c, "new email address",
                      "Your email address has been updated following your secure confirmation. A notification has been sent to your registered mobile.")
        _pcr(b, c, "email", "secure_chat", row["email_masked"], new_m, "completed", "Verified link and secure confirmation.")
        row["email_masked"] = new_m
        b.responds("profile_change_process", "email change request", "Completed after verification and secure confirmation.", ["status"], [])
        b.meta(title="Change of email asked from the new address", source_role="Bank customer", initial_request=ask,
               overview=f"A request to change {cs}'s email address came from the new, unverified address. {B} replied without acting or confirming anything and directed the sender to the app. "
                        f"{cs} then made the change through the secure process and confirmed it.",
               next_action="Reply without acting or disclosing anything; direct the sender to the app or a verified call.",
               outcome="The email address was updated after secure confirmation; the email itself was not acted on.", difficulty="tricky")
        b.label(decision_after=1, path="redirect_to_secure_route",
                first_action=("redirect_channel", "secure_chat", "Do not act on the email; direct the sender to the app's secure profile process."),
                gates=["authenticated_channel", "customer_confirmation_in_secure_channel", "untrusted_content_not_followed"],
                must_not=["change the email address on the strength of an email from that address", "confirm by email that the sender holds an account", NO_SECRETS],
                must_convey=["contact details cannot be changed by email", "use the app/secure portal or a verified call"],
                not_established=["that the sender is the customer"],
                outcome_state="redirected_then_email_changed", tags=["unauthenticated_channel", "account_takeover_risk", "redirect"])
        return

    ask = f"I've got a new email address and want to update it on my profile. It's {new_local}@{dom}."
    b.event(_conv(b), cs, agent, ask, "customer")
    b.event("Internal note", agent, proc,
            f"Opening the email-change process for {cs}, case {sc}. A verification link goes to the new address and a notification to the registered mobile. No change made yet.",
            "bank_agent")
    b.event(_conv(b), agent, cs,
            "I've started the change. You'll get a link at the new address and a confirmation step in your secure portal. "
            f"Nobody from {B} will ask you for a code or password to complete it.", "bank_agent")
    if v == "customer_offers_code":
        b.event(_conv(b), cs, agent, f"I've also had a text with a code — it's {code}. Do you need that?", "customer")
        b.event(_conv(b), agent, cs,
                "Thank you, but please don't share codes with anyone, including us; I haven't used it. You don't need it for this change. "
                "If you didn't ask for that code, tell me and I'll pass it to our security team.", "bank_agent")
        b.event(_conv(b), cs, agent, "No, it was from when I signed in. Sorry — I'll carry on in the portal.", "customer")
    b.event("Secure portal", c.full, proc, "I've opened the link and confirm the new email address in the secure process.", "customer")
    b.event("Secure portal", proc, c.full, "Your email address has been updated following your secure confirmation. A notification has been sent to your registered mobile.", "bank_system")
    _pcr(b, c, "email", "secure_chat", row["email_masked"], new_m, "completed", "Verified link and secure confirmation.")
    row["email_masked"] = new_m
    b.responds("profile_change_process", "email change request", "Completed after verification and secure confirmation.", ["status"], [])
    b.meta(title="New email address" if v == "secure_confirmed" else "Customer offers a one-time code",
           source_role="Bank customer", initial_request=ask,
           overview=f"{cs} asked to change {c.poss} email address in secure chat. The agent opened the secure change process; {c.subj} confirmed through the link and the portal."
                    + (" When the customer offered a one-time code, the agent declined it and warned against sharing codes." if v == "customer_offers_code" else ""),
           next_action="Open the email-change process; the customer confirms through the verification link and secure portal.",
           outcome="The email address was updated after secure confirmation." + (" The code was not used." if v == "customer_offers_code" else ""),
           difficulty="tricky" if v == "customer_offers_code" else None)
    b.label(decision_after=1, path="confirm_before_change",
            first_action=("send_for_customer_confirmation", "profile_change_process", "Open the email-change process for the customer's own secure confirmation."),
            gates=["authenticated_channel", "account_holder_or_owner", "customer_confirmation_in_secure_channel", "no_secrets_requested"],
            must_not=[NO_SECRETS, "change the email without the customer's confirmation"]
            + (["use, record or repeat the one-time code"] if v == "customer_offers_code" else []),
            must_convey=["change needs the customer's confirmation via link and portal", "bank never asks for codes"]
            + (["do not share codes", "code not used"] if v == "customer_offers_code" else []),
            not_established=["that the customer controls the new mailbox (until the link is used)"],
            outcome_state="email_changed", tags=(["secret_offered"] if v == "customer_offers_code" else []))


# ---------------------------------------------------------------------------
# 13. Title / preferred name / pronouns
# ---------------------------------------------------------------------------

@scenario("title_preferred_name", "profile", variants=["mx_title", "preferred_name", "pronouns", "remove_title"])
def title_preferred_name(b: CaseBuilder, v: str):
    if v == "mx_title":
        p = b.person("x")
        old_title = b.pick(["Ms", "Mr", "Miss", "Mrs"])
        c = b.new_customer(p, title=old_title)
    else:
        c = b.new_customer()
        old_title = c.title
    row = _cust_row(b, c)
    b.new_account(c)
    B, agent, cs = b.B, b.agent(), c.full
    sc = b.service_case_id()
    proc = b.sys("profile_change_process")
    pool = pools.FIRST_F if c.subj == "she" else pools.FIRST_M if c.subj == "he" else pools.FIRST_X
    middle = b.pick([n for n in pool if n != c.first])
    pron = f"{c.subj}/{c.obj}"
    ask = {
        "mx_title": f"Please change my title from {old_title} to Mx on all letters and in the app.",
        "preferred_name": f"Everyone calls me {middle} — it's my middle name. Can the app and your letters greet me as {middle}?",
        "pronouns": f"Can you note my pronouns on my profile? They're {pron}. Staff on the phone keep getting it wrong.",
        "remove_title": f"I don't want any title on my letters. Just “{c.full}”, please.",
    }[v]
    b.event(_ask_channel(b), cs, agent, ask, "customer")
    what = {"mx_title": "new title (Mx)", "preferred_name": f"preferred name ({middle})",
            "pronouns": f"pronouns ({pron})", "remove_title": "title setting (no title)"}[v]
    b.event("Internal note", agent, proc,
            f"Opening a profile update for {cs}, case {sc}: {what}. This is not a change of legal name, so no evidence is required; the customer will confirm in the secure process.",
            "bank_agent")
    limits = {
        "mx_title": "Your legal name is unchanged.",
        "preferred_name": f"Your legal name, {c.full}, will still appear on statements, cards and legal documents.",
        "pronouns": "The note is visible to staff who help you.",
        "remove_title": "Your legal name is unchanged.",
    }[v]
    b.event(_conv(b), agent, cs,
            f"I've started that for you. You'll see a confirmation step in your secure portal; once you confirm, we'll use it. You don't need to send any documents. {limits}",
            "bank_agent")
    _confirm_flow(b, c, what, f"Your profile has been updated with your {what}. This confirmation does not establish when letters already in preparation will reflect it.")
    field_new = {"mx_title": "Mx", "preferred_name": middle, "pronouns": pron, "remove_title": "(none)"}[v]
    _pcr(b, c, "name", _conv(b).lower().replace(" ", "_"), {"mx_title": old_title, "preferred_name": row["preferred_name"], "pronouns": None, "remove_title": old_title}[v],
         field_new, "completed", f"{what}; no legal name change.")
    if v == "mx_title":
        row["title"] = "Mx"
    elif v == "preferred_name":
        row["preferred_name"] = middle
    elif v == "pronouns":
        row["pronoun_hint"] = pron
    else:
        row["title"] = None
    b.responds("profile_change_process", "title/preferred name/pronoun update", f"Completed: {what}, after customer confirmation.",
               ["status"], ["letters already in preparation"])
    b.meta(title={"mx_title": "Title change to Mx", "preferred_name": "Greet me by my middle name",
                  "pronouns": "Recording my pronouns", "remove_title": "No title on my letters"}[v],
           source_role="Bank customer", initial_request=ask,
           overview=f"{cs} asked {B} to " + {"mx_title": f"use the title Mx instead of {old_title}", "preferred_name": f"greet {c.obj} by {c.poss} middle name, {middle}",
                                            "pronouns": f"record {c.poss} pronouns ({pron})", "remove_title": "stop using a title in letters"}[v]
                    + f". {B} treated it as a profile preference, not a legal name change, needing no evidence; "
                    f"the change was made after {c.subj} confirmed it in the secure process.",
           next_action="Open a profile update in the secure process for the customer's confirmation; no evidence needed.",
           outcome=f"Profile updated ({what}). The legal name is unchanged.")
    b.label(decision_after=1, path="confirm_before_change",
            first_action=("send_for_customer_confirmation", "profile_change_process", "Open the profile update for secure confirmation; no evidence required."),
            gates=["authenticated_channel", "account_holder_or_owner", "customer_confirmation_in_secure_channel"],
            must_not=["ask for legal name-change evidence for a title, preferred name or pronoun update", "question or comment on the customer's identity",
                      "use a different title, name or pronouns than the customer asked for", NO_SECRETS],
            must_convey=["no documents needed", "change applied after secure confirmation", "legal name unchanged"],
            not_established=["when letters already in preparation will reflect the change"],
            outcome_state="profile_preference_updated", tags=["identity_respect"])


# ---------------------------------------------------------------------------
# 14. Data protection: subject access and erasure
# ---------------------------------------------------------------------------

@scenario("data_request", "profile", variants=["subject_access", "sar_unverified_email", "erasure_open_account", "erasure_closed_account"])
def data_request(b: CaseBuilder, v: str):
    closed = v == "erasure_closed_account"
    c = b.new_customer(status="closed" if closed else "active")
    acc = b.new_account(c, **({"status": "closed", "closed_at": ts(b.days_before(b.rng.randrange(200, 1100), 12)),
                               "balance_minor": 0, "available_minor": 0, "history": False} if closed else {}))
    B, agent, cs = b.B, b.agent(), c.full
    sc = _service_case(b, c, "data_protection", "Erasure request" if v.startswith("erasure") else "Subject access request")
    dpt = b.sys("data_protection_team")
    recv = b.t0.date()

    if v in ("subject_access", "sar_unverified_email"):
        due = _add_months(recv, 1)
        if v == "sar_unverified_email":
            email = f"{c.first.lower()}{b.rng.randrange(10, 99)}@{b.pick(pools.EMAIL_DOMAINS)}"
            ask = f"Under data protection law I want a copy of all the personal data {B} holds about me, including call recordings. My name is {cs}, date of birth {_cust_row(b, c)['date_of_birth']}. Send it to this email."
            b.event("Email", f"{cs} <{email}>", f"{B} customer service", ask, "customer")
            b.event("Email", f"{B} customer service", email,
                    "Thank you for your request. Before we can handle a request for personal data we need to confirm your identity, and we can't confirm by email whether you hold an account with us. "
                    f"Please sign in to the {B} app or secure portal and make the request there, or visit a branch with identification. The one-month response period starts once your identity is confirmed. "
                    "We will not send personal data by email.", "bank_agent")
            dr = b.add("data_requests", data_request_id=b.world.next_id("DPR"), customer_id=c.id, kind="subject_access",
                       received_at=ts(b.events[0].at), due_at=None, status="identity_check_pending")
            b.event("Secure portal", cs, b.bank_name, "I'm signed in now. I want a copy of all the personal data you hold about me, as I asked by email.", "customer")
            recv = b.events[-1].at.date()
            due = _add_months(recv, 1)
            dr["status"] = "registered"
            dr["due_at"] = due.isoformat()
        else:
            ask = f"I want a copy of all the personal data {B} holds about me, including notes on my account and any call recordings."
            b.event(_conv(b), cs, agent, ask, "customer")
            dr = b.add("data_requests", data_request_id=b.world.next_id("DPR"), customer_id=c.id, kind="subject_access",
                       received_at=ts(b.events[0].at), due_at=due.isoformat(), status="registered")
        b.event("Internal note", agent, dpt,
                f"Subject access request from {cs}, identity confirmed by the authenticated session. Scope as stated: all personal data including account notes and call recordings. Case {sc}; request {dr['data_request_id']}.",
                "bank_agent")
        reply = f"Request {dr['data_request_id']} registered {long_date(recv)}. Response due by {long_date(due)}. Delivery via secure portal."
        b.event("Internal note", dpt, agent, reply, "bank_team")
        fname = f"data-request-acknowledgement-{b.case_number}.pdf"
        b.attach_pdf(fname, f"{b.bank_name.upper()} | SYNTHETIC DATA REQUEST ACKNOWLEDGEMENT",
                     [f"Reference {dr['data_request_id']} | {long_date(recv)}", f"Dear {c.formal}", "",
                      f"We received your request for a copy of your personal data on {long_date(recv)}, with your identity confirmed through your secure sign-in.",
                      f"We will respond by {long_date(due)}. If your request is complex we may extend this by up to two further months; if so, we will tell you why before {long_date(due)}.",
                      "We will deliver your data through your secure portal. We will not send it by email.",
                      "This letter acknowledges your request. It does not list or confirm the data we hold."],
                     description="Subject access request acknowledgement")
        b.event("Secure portal", b.bank_name, cs,
                f"We've registered your request for a copy of your personal data (reference {dr['data_request_id']}). We'll respond by {long_date(due)} and deliver it in your secure portal; "
                f"the acknowledgement is in {fname}. This doesn't yet confirm what data we hold.", "bank_system", attachments=[fname])
        if v == "subject_access":
            b.event(_conv(b), cs, agent, "Thanks. When it's ready, could you just email it to me instead? I find the portal fiddly.", "customer")
            b.event(_conv(b), agent, cs,
                    "I'm sorry the portal is awkward. We can't send personal data by email because it isn't secure, so your response will be in your secure portal. "
                    "If you'd prefer, you can ask for it to be made available for collection at a branch with identification.", "bank_agent")
        b.responds("data_protection_team", "register subject access request", reply, ["reference", "due date", "delivery route"], ["data held", "extension decision"])
        unver = v == "sar_unverified_email"
        b.meta(title="Copy of my personal data" if not unver else "Data request sent by email",
               source_role="Bank customer", initial_request=ask,
               overview=(f"A request for a copy of personal data arrived by unauthenticated email. {B} explained it needed identity confirmation and would not send data by email. "
                         f"{cs} then made the request in the secure portal, and the agent registered it" if unver else f"{cs} asked in secure chat for a copy of all personal data held, and the agent registered it")
                        + f" with the data protection team, which set a response date of {long_date(due)} and confirmed delivery via the secure portal.",
               next_action=("Reply without confirming any relationship; ask for the request through an authenticated channel." if unver
                            else "Register the subject access request with the data protection team."),
               outcome=f"Request {dr['data_request_id']} registered; response due {long_date(due)}. The content of the response is not yet established.",
               difficulty="tricky" if unver else None)
        b.label(decision_after=1, path="verify_then_act" if unver else "register_and_route",
                first_action=("verify_identity_or_authority", "authentication_service", "Ask the sender to confirm identity through an authenticated channel before registering.") if unver
                else ("register_case", "data_protection_team", "Register the subject access request with the data protection team."),
                gates=["authenticated_channel", "account_holder_or_owner"] + (["untrusted_content_not_followed"] if unver else []),
                must_not=["send personal data by email", "confirm the customer relationship over email", "refuse or discourage the request",
                          "promise what the response will contain", NO_SECRETS],
                must_convey=["registered with the data protection team", "one-month response timescale", "delivery via the secure portal"]
                + (["identity must be confirmed first", "timescale runs from identity confirmation"] if unver else []),
                not_established=["what data the bank holds", "whether call recordings still exist"],
                outcome_state="sar_registered", tags=["data_protection"] + (["unauthenticated_channel"] if unver else []))
        return

    # erasure
    ask = ("I want you to delete all the data you hold about me. I'm entitled to that under data protection law."
           if not closed else
           f"I closed my account with you on {long_date(dt.date.fromisoformat(acc['closed_at'][:10]))}. Please delete everything you hold on me and stop all marketing.")
    b.event("Secure chat" if not closed else "Verified call", cs, agent, ask, "customer")
    dr = b.add("data_requests", data_request_id=b.world.next_id("DPR"), customer_id=c.id, kind="erasure",
               received_at=ts(b.events[0].at), due_at=_add_months(recv, 1).isoformat(), status="registered")
    b.event(b.events[0].channel, agent, cs,
            "I can register that with our data protection team. I should be clear that we have to keep some records — for example account and transaction records and identity checks — "
            + ("for as long as your account is open and for a set period after it closes" if not closed else "for a set period after an account closes")
            + ", because the law requires it. The team will decide what can be deleted and tell you in writing. "
            + ("Closing your account would be a separate decision; deleting data doesn't close it. " if not closed else "")
            + "I can switch off marketing for you straight away, if you'd like.", "bank_agent")
    b.event(b.events[0].channel, cs, agent, "Yes, stop the marketing now, and register the deletion request.", "customer")
    b.event("Internal note", agent, dpt,
            f"Erasure request from {cs} ({'closed' if closed else 'open'} account), identity confirmed by the {'verified call' if closed else 'authenticated session'}. "
            f"Customer told that records the bank must retain cannot be deleted; marketing preferences switched off at the customer's request. Request {dr['data_request_id']}, case {sc}.",
            "bank_agent")
    reply = f"Request {dr['data_request_id']} registered. Response due {long_date(_add_months(recv, 1))}. Retained-record categories will be explained in the response."
    b.event("Internal note", dpt, agent, reply, "bank_team")
    b.event("Secure portal" if not closed else "Letter", b.bank_name, cs,
            f"We've registered your request to delete your personal data (reference {dr['data_request_id']}) and will respond by {long_date(_add_months(recv, 1))}. "
            "Some records must be kept for legal and regulatory reasons and can't be deleted; our response will explain what we keep and why. "
            "Marketing has been switched off. This message does not confirm that any data has been deleted.", "bank_system")
    b.responds("data_protection_team", "register erasure request", reply, ["reference", "due date"], ["which data will be deleted", "retention periods"])
    b.meta(title="Delete all my data" if not closed else "Delete my data after closing my account",
           source_role="Bank customer" if not closed else "Former customer", initial_request=ask,
           overview=f"{cs} asked {B} to delete all personal data held about {c.obj}"
                    + (" after closing the account" if closed else " while the account remains open")
                    + ". The agent explained that records the bank must keep cannot be deleted, switched off marketing at the customer's request, and registered the erasure request with the data protection team.",
           next_action="Register the erasure request with the data protection team and explain the limits on deletion.",
           outcome=f"Erasure request {dr['data_request_id']} registered; marketing switched off. No data has been confirmed deleted.",
           difficulty="tricky")
    b.label(decision_after=1, path="register_and_route",
            first_action=("register_case", "data_protection_team", "Register the erasure request and explain that legally required records are kept."),
            gates=["authenticated_channel", "account_holder_or_owner"],
            must_not=["promise that all data will be deleted", "delete or close anything unilaterally", "refuse to register the request", NO_SECRETS]
            + (["imply that deleting data closes the account"] if not closed else []),
            must_convey=["request registered with reference", "some records must be kept by law", "one-month response", "marketing can be stopped now"],
            not_established=["which data will be deleted", "exact retention periods for this customer"],
            outcome_state="erasure_registered", tags=["data_protection", "retention_limits"] + (["former_customer"] if closed else []))


# ===========================================================================
# COMPLAINTS
# ===========================================================================

@scenario("formal_complaint", "complaints",
          variants=["service_delay", "mentions_ombudsman", "fee_complaint", "staff_conduct", "venting"])
def formal_complaint(b: CaseBuilder, v: str):
    c = b.new_customer()
    acc = b.new_account(c)
    B, agent, cs = b.B, b.agent(), c.full
    sc = _service_case(b, c, "complaints", "Complaint")
    fee = None
    issue_day = b.days_before(b.rng.randrange(10, 30))
    delay_topic = b.pick(["an address change", "a replacement card", "an archived statement", "a Direct Debit cancellation"])
    if v == "fee_complaint":
        fee = _fee(b, acc, b.pick(["returned_item", "paper_statement", "chaps"]), issue_day)
    branch = b.pick(pools.TOWNS)[0]
    subject = {
        "service_delay": f"Delay and repeated chasing over {delay_topic} request made on {long_date(issue_day)}",
        "mentions_ombudsman": f"Unhappy with handling of {delay_topic} request made on {long_date(issue_day)}",
        "fee_complaint": f"{_cap(FEE_PLAIN[fee['fee_type']])} of {money(fee['amount_minor'])} charged on {long_date(issue_day)}" if fee else "",
        "staff_conduct": f"Treatment by staff at the {branch} branch on {long_date(issue_day)}",
        "venting": f"Repeated failed attempts to get {delay_topic} request dealt with",
    }[v]
    ask = {
        "service_delay": f"I want to make a formal complaint. I asked for {delay_topic} on {long_date(issue_day)} and I've chased it three times since. Nobody has sorted it.",
        "mentions_ombudsman": f"I've had enough. My request for {delay_topic} from {long_date(issue_day)} still isn't done. I'm going straight to the ombudsman — there's no point complaining to you.",
        "fee_complaint": f"I want to complain about the {money(fee['amount_minor']) if fee else ''} fee you charged on {long_date(issue_day)}. It's unfair and I want it refunded.",
        "staff_conduct": f"I want to complain about how I was treated at your {branch} branch on {long_date(issue_day)}. The person at the counter was dismissive and talked over me in front of other customers.",
        "venting": f"This is ridiculous. Third time I've tried to get {delay_topic} sorted and your app just goes round in circles. Nobody ever gets back to me. I'm so fed up with {B}.",
    }[v]
    if v in ("service_delay", "mentions_ombudsman"):
        b.event("Secure portal", b.bank_name, cs,
                f"Your request for {delay_topic}, received on {long_date(issue_day)}, is still in progress. This message does not give a completion date.", "bank_system")
    if v == "mentions_ombudsman":
        b.event("Secure chat", cs, agent, f"It's been weeks since I asked for {delay_topic}. Can someone actually tell me what's happening?", "customer")
    if v == "fee_complaint":
        b.event("Secure portal", b.bank_name, cs, f"A {money(fee['amount_minor'])} {FEE_PLAIN[fee['fee_type']]} dated {long_date(issue_day)} has been applied to your account.", "bank_system")
    b.event("Secure chat" if v != "staff_conduct" else "Verified call", cs, agent, ask, "customer")
    received = b.events[-1].at
    due = received.date() + dt.timedelta(weeks=8)
    cmp = b.add("complaints", complaint_id=b.world.next_id("CMP"), customer_id=c.id, business_id=None, received_at=ts(received),
                subject=subject, status="acknowledged", final_response_due=due.isoformat(), ombudsman_rights_given=1)
    if fee:
        fee["review_status"] = "under_review"
    reply_intro = {
        "service_delay": "I'm sorry you've had to chase this. I'm registering it as a formal complaint now.",
        "mentions_ombudsman": ("I'm sorry about this. You're entitled to go to the Financial Ombudsman Service, and I won't stop you. "
                               "The Ombudsman will normally expect us to have had the chance to respond first, so I'm registering your complaint with our complaints team now; "
                               "you can refer it to the Ombudsman once you have our final response, or if 8 weeks pass without one."),
        "fee_complaint": "I'm registering this as a formal complaint now. I can't refund the fee myself or promise the outcome; the complaints team will look at it.",
        "staff_conduct": "I'm sorry about how that felt. I'm registering this as a formal complaint so our complaints team can look into it.",
        "venting": "I'm sorry — that's not the experience you should have. What you've described is a complaint, so I'm registering it with our complaints team; they will look at the outstanding request as part of it.",
    }[v]
    b.event("Secure chat" if v != "staff_conduct" else "Verified call", agent, cs, reply_intro, "bank_agent")
    b.event("Internal note", agent, b.sys("complaints_team"),
            f"Registering a complaint from {cs}: {subject}. Received {ts(received)} UTC via {'verified call' if v == 'staff_conduct' else 'secure chat'}. "
            + ("Customer did not use the word 'complaint'; recorded as an expression of dissatisfaction. " if v == "venting" else "")
            + ("Customer has mentioned the Financial Ombudsman Service. " if v == "mentions_ombudsman" else "")
            + f"No outcome, refund or compensation promised. Case {sc}.", "bank_agent")
    reply = f"Complaint {cmp['complaint_id']} registered and acknowledged. Final response due by {long_date(due)}. Ombudsman referral rights included in the acknowledgement."
    b.event("Internal note", b.sys("complaints_team"), agent, reply, "bank_team")
    fname = f"complaint-acknowledgement-{b.case_number}.pdf"
    _doc(b, acc, c, "complaint_acknowledgement", "delivered_to_portal", fname)
    b.attach_pdf(fname, f"{b.bank_name.upper()} | SYNTHETIC COMPLAINT ACKNOWLEDGEMENT", [
        f"Complaint reference {cmp['complaint_id']} | {long_date(received)}", f"Dear {c.formal}", "",
        f"We received your complaint on {long_date(received)}. Subject of your complaint: {subject}.",
        f"Our complaints team will investigate and send you a final response by {long_date(due)} at the latest (8 weeks from receipt).",
        "If we cannot do so, we will write to explain why and when we expect to respond.", "",
        f"If you are unhappy with our final response, or you have not received it within 8 weeks, you may be able to refer your complaint to the {FOS}.",
        "Its service is free. You normally have six months from the date of our final response to refer your complaint.", "",
        "This letter acknowledges your complaint. It does not decide it, and does not confirm any finding, refund or compensation."],
        description="Complaint acknowledgement letter")
    b.event("Secure portal", b.bank_name, cs,
            f"We've registered your complaint (reference {cmp['complaint_id']}). The acknowledgement letter is in your secure portal as {fname}. "
            f"We'll send our final response by {long_date(due)}. If you're unhappy with it, or don't have it by then, you may be able to refer your complaint to the {FOS}, free of charge. "
            "This acknowledgement doesn't decide the complaint.", "bank_system", attachments=[fname])
    if v == "staff_conduct":
        b.event(_conv(b), cs, agent, "Will the staff member be disciplined? I want to know what happens to them.", "customer")
        b.event(_conv(b), agent, cs,
                "The complaints team will look into what happened and explain their findings in the final response. I can't share details about individual staff members or any internal action.",
                "bank_agent")
    b.responds("complaints_team", "register complaint", reply, ["reference", "final response due date"], ["finding", "outcome", "redress"])
    if fee:
        b.responds("fee_tariff", "fee basis", f"{FEE_PLAIN[fee['fee_type']]} {money(fee['amount_minor'])}, tariff {fee['tariff_ref']}: {fee['basis_text']}", ["basis"], [])
    if v == "staff_conduct":
        b.responds("case_record", "branch visit notes", f"No notes are recorded for a branch visit by {cs} on {long_date(issue_day)}.", [], ["what was said", "staff member's identity"])
    b.meta(title={"service_delay": "Formal complaint about a delay", "mentions_ombudsman": "Going straight to the ombudsman",
                  "fee_complaint": "Complaint about a fee", "staff_conduct": "Complaint about a branch visit",
                  "venting": "Frustrated message — is it a complaint?"}[v],
           source_role="Bank customer", initial_request=ask,
           overview=f"{cs} expressed dissatisfaction about: {subject[:1].lower() + subject[1:]}. "
                    + ("The message did not use the word 'complaint', but it was treated as one. " if v == "venting" else "")
                    + f"{B} registered it with the complaints team, gave the reference {cmp['complaint_id']}, explained the 8-week final-response timescale and the right to refer to the {FOS}, "
                    "and placed the acknowledgement letter in the secure portal.",
           next_action="Register the complaint with the complaints team and give the reference, timescale and ombudsman rights.",
           outcome=f"Complaint {cmp['complaint_id']} acknowledged; final response due by {long_date(due)}. No finding, refund or compensation has been decided.",
           difficulty={"venting": "tricky", "mentions_ombudsman": "tricky", "staff_conduct": "tricky"}.get(v))
    must_not = ["promise an outcome, refund or compensation", "discourage or obstruct a referral to the Financial Ombudsman Service", NO_SECRETS]
    if v == "venting":
        must_not += ["treat the message as not a complaint because the word 'complaint' was not used"]
    if v == "staff_conduct":
        must_not += ["disclose staff details or any disciplinary action", "agree or disagree with the account of what was said"]
    if v == "fee_complaint":
        must_not += ["refund the fee unilaterally"]
    b.label(decision_after={"fee_complaint": 2, "service_delay": 2, "mentions_ombudsman": 3}.get(v, 1), path="register_and_route",
            first_action=("register_case", "complaints_team", "Register the expression of dissatisfaction as a complaint with the complaints team."),
            gates=["authenticated_channel", "account_holder_or_owner"], must_not=must_not,
            must_convey=["complaint registered with reference", "final response within 8 weeks (by the due date)",
                         "right to refer to the Financial Ombudsman Service (free)", "acknowledgement does not decide the complaint"],
            not_established=["the complaint's outcome", "that the bank was at fault"]
            + (["what the staff member said or did", "the staff member's identity"] if v == "staff_conduct" else [])
            + (["that the fee will be refunded"] if v == "fee_complaint" else []),
            signposts=[FOS], outcome_state="complaint_registered",
            tags={"venting": ["implicit_complaint", "emotional"], "mentions_ombudsman": ["ombudsman_mentioned"],
                  "staff_conduct": ["staff_complaint", "third_party_data"], "fee_complaint": ["fee"]}.get(v, []))
