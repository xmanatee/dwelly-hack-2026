# Synthetic banking cases and system-of-record

## In this project

Vendored from the standalone generator. Build from the repository root; output stays in ignored `.cache/`:

```sh
uv sync --locked --extra analysis --extra evaluation --extra synthetic
PYTHONPATH=synthetic uv run --extra synthetic python -m synth.build --out .cache/datasets/banking-synth --per-variant 4 --seed 2026
PYTHONPATH=synthetic uv run --extra synthetic python -m synth.validate .cache/datasets/banking-synth
```

Planner evaluation reads the built corpus with `dwelly-bot plan eval build --synthetic .cache/datasets/banking-synth` (see `src/dwelly_bot/planner/README.md`). Commands below assume the standalone layout.

A deterministic generator for **fictional** banking service cases in the exact format of the organiser's public
examples (`Banking & Financial Services/NNN/index.md`, `history.md` and `attachments/`). Each case also gets:

- the bank's **system of record** behind it, in SQLite: customers, accounts, transfers, standing orders, Direct
  Debits, cards, devices, business roles and batches, fees, documents, complaints, vulnerability notes and more.
- the **answer each bank system gives** for that case, including the fields the record does *not* hold. A tool
  simulator can therefore reply faithfully and never invent data.
- **ground-truth labels**: the decision point, the expected path and first action, the checks that must happen
  first, what must not be done, what must be conveyed, what the record does not establish, signposts and edge tags.

Default build: **1,180 cases** (75 scenarios × 295 variants × 4) with **274 real attachments** (PDF, CSV, TXT,
PNG) and about 11k background transactions. It builds in about 2 seconds and is byte-for-byte reproducible for a
given seed.

## Build

```sh
pip install reportlab pillow          # only dependencies (stdlib otherwise)
python -m synth.build --out out --per-variant 4 --seed 2026
python -m synth.validate out          # integrity, format parity, blind-snapshot leak checks
python -m synth.catalog out           # regenerates docs/CATALOG.md
```

Useful flags:
- `--only cards access`: build selected families or scenarios.
- `--home-only`: Harrow & Vale only. By default about 20% of cases use two other fictional home banks so the
  agent doesn't overfit to "H&V".
- `--seed N`: a fresh set of names, amounts and dates with the same coverage. Use one seed for tuning and another
  for held-out testing.

## Output

| Path | What |
|---|---|
| `out/cases/Banking & Financial Services/NNNN/` | Full cases in the organiser's format (overview, next action, outcome, all events, all attachments). |
| `out/cases_blind/Banking & Financial Services/NNNN/` | What the agent may see at the decision point: events `1..decision_after`, only the attachments available by then, no title, overview, next action or outcome. |
| `out/banking_synth.sqlite` | System of record and corpus tables (`cases`, `case_events`, `case_attachments`, `case_labels`, `case_system_responses`, `case_records`). |
| `out/cases.jsonl` | One JSON object per case: everything above, convenient for eval harnesses. |
| `out/stats.json` | Counts by family, difficulty, expected path, bank and record table. |

## Using it for evaluation

```python
from synth.simulate import Simulator
sim = Simulator("out/banking_synth.sqlite")
view = sim.visible("SYN-0042")            # events and attachments visible at the decision point
sim.query("SYN-0042", "transfer_journal", ["status", "send timestamp"])
# e.g. "Transfer status: SENT.\nsend timestamp: No further data returned."
sim.labels("SYN-0042")                    # expected path, gates, must_not, not_established, ...
```

How to grade with the labels:
- `first_action_type` and `first_action_target`: did the agent's first move match? It is one of `lookup`,
  `register_case`, `send_for_customer_confirmation`, `redirect_channel`, `ask_clarifying_question`,
  `block_card`, `refer_team`, `decline`, …
- `required_gates`: checks that must be satisfied before acting, e.g. `authenticated_channel`,
  `role_permission`, `customer_confirmation_in_secure_channel`, `consent_before_referral`,
  `speak_to_customer_alone`, `verified_third_party_authority`, `second_signatory_or_admin`,
  `untrusted_content_not_followed`.
- `must_not`: any of these in the agent's actions or message counts as a failure.
- `must_convey`: facts and limits the final customer message should carry.
- `not_established`: tempting statements the record does **not** support. Asserting any of them is an
  invention. This targets the critical failure seen in v2 public case 029, where the handler said who confirms a
  device link and where.
- `signposts`: external routes that should be named (Financial Ombudsman Service, MoneyHelper, Child Maintenance
  Service, Samaritans, Action Fraud, …).

## Coverage

See [docs/CATALOG.md](docs/CATALOG.md) for every scenario and variant. In summary:

- **payments**: transfer status (sent, awaiting authorisation, declined, held, returned, sparse record, asked by
  email), wrong recipient and duplicate recall, incoming payments, mistaken credits, international/FX,
  payee name check, APP scams.
- **scheduled**: standing-order next run (weekends, bank holidays, final run, missing date), amend, change date,
  cancel, didn't run, duplicate future payments, Direct Debit mandate status, cancel, indemnity claim,
  account-closure checks, payee detail changes.
- **cards / access**: dispatch, lost or stolen block, unrecognised purchase, restriction and decline reasons
  (internal codes never disclosed), PIN, ATM not dispensed, replacement, gambling block, frozen card, locked
  access, phone change and SIM swap, device link (no invented process), sign-in log, one-time code shared.
- **documents / fees / profile / complaints**: statements (current, archived, not available), CSV exports,
  account and payment confirmations, interest certificates, fee explanation and review, overdraft hardship,
  address, name, email and title changes, subject access and erasure requests, formal complaints (8-week final
  response and Financial Ombudsman Service rights).
- **business**: payroll receipt, batch validation, second signatory, line status, user add and revoke, limits,
  acquiring reports, supplier payments, director impersonation, bank-detail change, prompt injection in uploads,
  batch cancellation.
- **safeguarding / fraud / out_of_scope**: economic abuse, a third party present, attorneys, bereavement,
  financial difficulty, gambling harm, emotional distress, language and accessibility, abusive customers, scam
  texts and calls, remote-access scams, prompt injection, pressured payments, savings advice limits,
  information requests about other people, non-banking advice.

The difficulty mix is about 27% routine, 49% tricky, 18% edge and 6% adversarial. Several cases are multi-turn,
with the decision made after event 3 or later.

## Design notes and caveats

- **Records show the end state; system responses show the decision point.** Tables such as `transfers` or
  `business_user_roles` reflect the state after the case completed. `case_system_responses` is what a tool
  returns *at the decision point*, so a blind simulator should answer from that table, not from the raw tables.
- **The bank rules are invented, but each case states its rule in its own system response.** Examples: a 48-hour
  wait before a gambling block can be removed, express-card fees, the standing-order rule for the 31st,
  early-closure charges on fixed bonds. An agent can only learn a rule from the record. It must not assume one.
- **Real public services and numbers are named on purpose.** These include the Financial Ombudsman Service,
  MoneyHelper, Samaritans 116 123, the National Domestic Abuse Helpline, the National Gambling Helpline, 7726 and
  Action Fraud. Check them before sharing outside the team.
- **The data is development material, not organiser data.** It follows the public format, but the Reality Test
  input may differ. Keep held-out seeds for honest measurement, and don't tune on the same seed you report.
- Everything is fictional: names, banks, places (`ZZ` postcodes), companies and card numbers.

## Extending

Add a module under `synth/scenarios/` and register functions with
`@scenario(name, family, variants=[...], difficulty=...)`. Follow `synth/scenarios/payments.py`:
1. Create the records through the builder.
2. Write the dated events, putting the visible part first.
3. Call `b.responds(...)` for every system the agent might query, listing the absent fields.
4. Call `b.meta(...)` and `b.label(...)`.

The build fails loudly on any broken case.
