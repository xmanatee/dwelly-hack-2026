# Local banking world

[← Project](../../README.md)

Three acceptance checks:

- [ ] **Data:** reproducible state, separate incoming cases, isolated evaluator answers.
- [ ] **Context:** resolve local contact hints, read case threads and relevant bank systems,
  preserve missing fields, exclude other cases and future state.
- [ ] **Bot:** run email, call and ticket through the shared collector → Planner → executor,
  capture `context.md`, plan, receipts and tool journal; replay without duplicate mock effects.

The supplied archive contains Nikita's generator, not a built dataset. Its original source
is preserved in `generator/` (excluding the embedded Git repository); `source.json` pins
every imported file and the archive. The seed-2026 build contains 1,180 cases, 75 scenarios,
295 variants, 1,020 customers, 1,248 accounts and 11,063 background transactions.

## Build the data

From the repository root:

```sh
uv run --extra evaluation --with reportlab==5.0.1 --with pillow==12.3.0 \
  python local_testing/banking/build.py
```

Use `--seed 2027 --output local_testing/banking/data/held-out` for a separate world.
Existing output directories are refused. Generated data stays local and ignored; teammates
rebuild from the committed source. PDFs use `pypdf` from the evaluation extra; PNGs are
retained with an explicit unsupported-text warning (no invented OCR).

```text
data/seed-2026/
├── state/
│   ├── decision.sqlite     # only decision-time messages, contacts and system responses
│   ├── attachments/        # only attachments available by the cutoff
│   └── end-state.sqlite    # relational banking tables AFTER completion; inspection only
├── cases/SYN-*.json        # incoming request + trusted scenario scope + reply route
├── evaluation/original/    # untouched full histories, labels, original database and files
└── manifest.json           # hashes, counts and extraction coverage
```

**The source's entity tables are final state.** A cancelled payment or changed customer
profile may already be reflected there. The runtime therefore reads recorded decision-time
bank-system responses, following the generator's own simulation contract. It never opens
`end-state.sqlite` or `evaluation/`. Those tables provide realistic schema examples, but a
fully temporal entity store is still a future generator improvement.

Some response templates describe completed **commands**, even under a system marked
read-only (for example, `card_system / block card`). The reviewed
[read-query allowlist](../../src/dwelly_bot/adapters/synthetic_banking/read_queries.json)
excludes command results, mixed read/write responses and new unreviewed query types.
They remain in the original archive. This deliberately leaves gaps rather than asserting
that an action has already happened. The importer does not use evaluator answers to fill them.

Incoming cases use the last visible customer/third-party/external message; the trigger time
is the scenario decision point. Earlier visible messages remain a thread. Secure chat,
portal and other unsupported transports are wrapped as local tickets, preserving original
channel, actor and authentication flags. Email/call events retain their corresponding route.

The original contacts are masked. Local `.invalid` email addresses and unassigned `+999`
phone aliases are explicitly generated to exercise lookup and routing. A matching alias or
name does not authenticate a person. Scenario scope comes from the trusted local runner.

## Run the bot

```sh
uv run dwelly-bot local list --limit 10
uv run dwelly-bot local run --case SYN-0001 --output .cache/local-bank/ticket-demo
uv run dwelly-bot local run --case SYN-0250 --channel call --output .cache/local-bank/call-demo
uv run dwelly-bot local run --case SYN-0813 --channel email --output .cache/local-bank/email-demo
```

Default mode reads the available scoped snapshots deterministically and uses the human-review
Planner. It needs no keys. `--channel` replays the same evidence through another local
transport, explicitly labelled; it does not convert the original session into a newly
authenticated one. All external actions remain mock.

For the intelligent collector, set `ANTHROPIC_API_KEY` in the existing `.env` and use:

```sh
uv run dwelly-bot local run --case SYN-0250 --channel call \
  --context-config experiments/synthetic-context-integration/config.json \
  --output .cache/local-bank/context-agent
```

The investigator chooses `read_source(source, question)` calls from a catalogue of contact,
thread, document and bank-system sources. The adapter fixes scope and snapshot time; the
model cannot change them or execute SQL. It reports information needs and gaps, while the
collector preserves retrieved records in a single `context.md` for Planner. Model settings,
tool calls and costs use the existing shared runtime and journal.

Use `--input PATH` instead of `--case` for your own email/call/ticket JSON (same contract as
`cases/SYN-*.json`). Keep its trusted `scope_id` and a timestamp at or after that scenario's
snapshot. A phone/email/name identifies a candidate only within that scope. This local
entry point trusts your JSON; it is not a public webhook authentication layer.

`--plan PATH` injects a fixture plan for executor tests. `--state PATH` chooses the durable
mock receipt database; by default `.cache/local-bank/receipts.sqlite`. A repeated event and
plan reuse receipts. Always use a fresh `--output` directory. Each run saves input, normalized
trigger, context text/records, plan, action receipts, local journal and dataset hashes.

No ElevenLabs key is needed yet: call triggers contain transcripts and session metadata.
The future voice adapter can submit the same input contract.

## Inspect the data

```sh
uv run dwelly-bot analyze run dwelly_bot.analysis.synthetic_bank \
  --data local_testing/banking/data/seed-2026
```

This offline report counts runtime snapshots, messages and documents; it does not read
labels or final entity state. Current seed: 2,088 visible messages, 1,400 reviewed read
responses, 495 withheld action/mixed/unreviewed responses. 188/1,180 cases have no retained
bank response and expose that gap. Of 130 visible attachments, 56 are plain text/CSV,
28 yield PDF text and 46 PNGs are retained but not read. The other 144 attachments are later.

[Functional verification and live context receipts](../../experiments/synthetic-context-integration/README.md).
