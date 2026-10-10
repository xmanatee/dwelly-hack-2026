# Hackathon Winner folder integration

Requested migration: the contest runner sits in `src/hackathon_winner`, beside `dwelly_bot`,
and imports Vera's existing `dwelly_bot.planner`. No new Planner implementation or executable
bank actions are introduced. A supplied case folder becomes a same-named output folder with
ANSWER.md, REASONING.md, saved context, plan and generation receipts.

Hypothesis: the independent folder runner can reuse the real Planner and shared model/runtime
infrastructure, generate an evidence-based operator memo, and preserve failures without
requiring the product's trigger/context/executor composition.

The default config uses the project's configured Anthropic Sonnet API. Vera's Claude Code Sonnet transport remains a separate config. Output defaults to repository
ANSWERS/; `--output` selects an evaluation destination. The two included inputs are fictional
smoke cases, not organizer data. The adapter reads supplied history/context/request and
attachments; it does not read index.md or evaluator answers. The caller provides the intended
snapshot boundary. Output names and default destination implement the user's current request;
older practice-only export restrictions remain on the separate saved-execution exporter.

Validation: targeted offline tests exercise no-flag/default output, a custom output folder,
original case IDs, raw context fallback, attachments, path boundaries, public Planner imports,
model failures and non-overwrite behavior. Live verification uses committed configurations and the two bundled cases, preserving actual generated results and journal messages.

The existing baseline does not match the current runtime. This is integration verification,
not a paired quality experiment or baseline adoption. Historical baseline bytes remain intact.


The first live attempt at source `da0f0fb` used Claude Code Sonnet and failed both Planner
calls with an invalid OAuth access token (401). The two actual failure outputs and journals
are retained in `claude-code-captures.json.gz`, with their original HTML report. No generator
ran. The default config was then changed to the already configured Anthropic API, preserving
the existing account ledger. No credential file or CLI login was modified.


## Verified outcome

- Full offline gate: **305 tests**, Ruff and strict mypy (150 source files).
- Built wheel includes both modules, Planner resources, Winner configurations and smoke data.
- Source `d0d0b7d`: both bundled cases completed Planner → model generator, with 4 settled model requests and estimated API cost **$0.090032**.
- [Actual outputs](report.html), [verification receipt](verification.json) and `anthropic-captures.json.gz` retain the generated answers, reasoning, plans, source context and traces.
- The failed Claude Code attempt remains separately saved; no generated case was manually corrected.

The second plan still proposes a journal re-check despite the supplied journal snapshot.
This remains visible in its plan and reasoning; tuning Planner decisions is separate from
verifying the import/export path. No quality improvement or official test score is claimed.
