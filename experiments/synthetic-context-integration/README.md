# Synthetic context integration

Hypothesis: the existing read-only Pydantic AI investigator can select bank-system sources,
resolve a local contact and gather a case thread without receiving evaluator labels or
post-action entity state. The Planner remains the human-review stub.

Change: a separate synthetic-world importer, reviewed read-query projection, scoped source
adapters and a local runner using the shared production pipeline/model pool/budget/journal.

Validation scope: offline source/boundary/routing/replay tests and three live context-only
smoke runs (ticket, email and call). This is a functional integration check, not a quality
benchmark or evidence that one Planner is better than another. No full-bank model sweep.

The pre-edit baseline check failed because the historical baseline does not represent
current production code. Its reference and results are preserved. This new synthetic corpus
requires its own future baseline before an improvement comparison or baseline adoption.

Model config: [config.json](config.json), Sonnet through the existing Anthropic account ledger.
The inherited account cap preserves prior charges/reservations; it is not fresh credit.
No voice provider or external banking/communication service is used. Actual validation
receipts and any failures will be recorded here after the smoke runs.
