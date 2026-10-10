# Local banking world

[← Project](../../README.md)

Three acceptance checks:

- [x] **Data:** reproducible state, separate incoming cases, isolated evaluator answers.
- [x] **Context:** resolve local contact hints, read case threads and relevant bank systems,
  preserve missing fields, exclude other cases and future state.
- [x] **Bot:** run email, call and ticket through the shared collector → Planner → executor,
  capture `context.md`, plan, receipts and tool journal; replay without duplicate mock effects.

The supplied archive contains Nikita's generator, not a built dataset. Its original source
is shared in [`synthetic/`](../../synthetic/README.md) (excluding the embedded Git repository);
`source.json` pins every originally imported file and the archive. The upstream generator
code matches those hashes; its extended README is separate from our preserved
[`source-README.md`](source-README.md). The seed-2026 build contains 1,180 cases, 75 scenarios,
295 variants, 1,020 customers, 1,248 accounts and 11,063 background transactions.

## Build the data

From the repository root:

```sh
uv run --extra synthetic --extra evaluation \
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
model cannot change them or execute SQL. The collector preserves retrieved records, actual read questions and source-reported gaps
in a single `context.md` for Planner. Free-form model notes remain in the journal. Model settings,
tool calls and costs use the existing shared runtime and journal.

Use `--input PATH` instead of `--case` for your own email/call/ticket JSON (same contract as
`cases/SYN-*.json`). Keep its trusted `scope_id` and a timestamp at or after that scenario's
snapshot. A phone/email/name identifies a candidate only within that scope. This local
entry point trusts your JSON; it is not a public webhook authentication layer.

`--plan PATH` injects a fixture plan for executor tests. `--state PATH` chooses the durable
mock receipt database; by default `.cache/local-bank/<dataset-hash>/receipts.sqlite`, isolating different seeds. A repeated event and
plan reuse receipts. Always use a fresh `--output` directory. Each run saves input, normalized
trigger, context text/records, plan, action receipts, local journal and dataset hashes.

No ElevenLabs key is needed for these local call replays: triggers contain transcripts and
session metadata. A separate [live voice runner](../../demo/LIVE-DEMO.md) already connects
ElevenLabs to normalized JSON/SQLite sources and a fixture plan. It does not directly load
this synthetic dataset or expose the model Planner; the model-backed HTTP service is a
separate integration.

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

Acceptance evidence: 27 affected offline tests, strict types and Ruff; the full 1,180-case
seed-2026 build and a fresh 295-case seed-2028 build passed generator integrity checks.
Three live context smokes were inspected, fixed, repeated and repeated again after
team synchronization; all nine captures remain saved. A further 36-test combined check passed. This establishes integration mechanics, not corpus-wide retrieval or Planner quality.

Team synchronization consolidated the duplicate generator into `synthetic/`. The build now
uses the existing locked `synthetic` dependency extra. Earlier captures retain their original
ReportLab 5.0.1 receipt; fresh builds record their installed versions in `manifest.json`.
The offline default uses `dwelly_bot.planning.HumanReviewPlanner`. Add
`--planner-config src/hackathon_winner/config.json` to call the shared
[`dwelly_bot.planner`](../../src/dwelly_bot/planner/README.md) through `DecisionPlanner`.
Its full canonical plan is preserved and handled by `DecisionExecutor` in mock mode.
`--context-config` independently enables model-directed evidence collection.

New builds publish only after the entire projection succeeds and include `cases_sha256`
checksums for incoming trigger files. The runner verifies these alongside the database and
read-query policy. Legacy v1 datasets without that field remain supported; their manifest
checks the database, not individual trigger bytes. Build to a fresh directory to obtain full
trigger checksums. Original data and earlier captures are never upgraded in place.

Failed pipeline runs retain `dataset.json` with the partial context and failure receipt.
Keep `--state` outside `--output`; channel replay requires one unambiguous local contact.
A failed source read becomes an explicit gap, while other observed evidence is retained.

For an independent model/config experiment on the same event, pass a fresh `--state`
SQLite path outside `--output`. Reusing the normal receipt store correctly rejects changed
actions for an already processed event; a new capture directory does not reset that state.
