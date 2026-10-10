# Hackathon Winner folder integration

Requested migration: the contest runner sits in `src/hackathon_winner`, beside `dwelly_bot`,
and imports Vera's existing `dwelly_bot.planner`. No new Planner implementation or executable
bank actions are introduced. A supplied case folder becomes a same-named output folder with
ANSWER.md, REASONING.md, saved context, plan and generation receipts.

Hypothesis: the independent folder runner can reuse the real Planner and shared model/runtime
infrastructure, generate an evidence-based operator memo, and preserve failures without
requiring the product's trigger/context/executor composition.

The default config retains Vera's Claude Code Sonnet transport. Output defaults to repository
ANSWERS/; `--output` selects an evaluation destination. The two included inputs are fictional
smoke cases, not organizer data. The adapter reads supplied history/context/request and
attachments; it does not read index.md or evaluator answers. The caller provides the intended
snapshot boundary. Output names and default destination implement the user's current request;
older practice-only export restrictions remain on the separate saved-execution exporter.

Validation: targeted offline tests exercise no-flag/default output, a custom output folder,
original case IDs, raw context fallback, attachments, path boundaries, public Planner imports,
model failures and non-overwrite behavior. Live verification uses the committed default
config and the two bundled cases, preserving actual generated results and journal messages.

The existing baseline does not match the current runtime. This is integration verification,
not a paired quality experiment or baseline adoption. Historical baseline bytes remain intact.
