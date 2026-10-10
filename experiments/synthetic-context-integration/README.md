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
No voice provider or external banking/communication service is used.

## Inspected result

[Open the saved report](report.html) · [Machine-readable checks](verification.json)

| Case | Transport | Observed retrieval |
| --- | --- | --- |
| SYN-0001 | Ticket | Three-message thread, contact candidate, fee tariff; missing fee-review/complaint snapshots recorded as gaps. |
| SYN-0250 | Call replay | Contact candidate, two-message thread, returned-undelivered card dispatch record with absent return date/reason. |
| SYN-0813 | Email | Contact candidate, original unauthenticated email, phone-change request recorded as not actioned. |

Initial source `1361cec`: all three completed, but free-form research notes called a local
phone alias an on-file number and missing simulator responses absent bank records.
The notes were reaching the Planner's needs/gaps sections.

Revised source `a90f099`: source records are unchanged, except clearer transport-alias
metadata. Only actual source questions and source warnings are forwarded; model notes
remain in the journal. Three fresh model runs passed scope/time, observed-record and
source-only-warning checks. Retrieval returned 5/4/3 records respectively. The model may
still omit useful sources; this small check does not measure completeness.

Both revisions use identical inputs/configuration. Seven model requests per revision;
14 total; **$0.106335 estimated total** from the configured-price ledger. No failed model
requests occurred. Early problematic outputs are retained, not rewritten. Planner decisions
remain a fixed handoff; execution is mock (some receipts are replays from earlier local runs).

Saved raw captures: `initial-captures.json.gz`, `revised-captures.json.gz`. To verify and
rerender without model calls:

```sh
uv run python experiments/synthetic-context-integration/review.py
```

Other evidence: 27 affected offline tests passed; full strict typing and Ruff passed.
The importer excluded 495 action/mixed/unreviewed responses and preserved 1,400 reads.
The local CLI additionally isolates its default mock receipt store by runtime database
hash, so distinct generated seeds cannot collide through identical SYN case IDs. This
receipt-path adjustment is verified offline; it does not change model inputs or retrieval.

Conclusion: the requested local integration is implemented. No historical baseline was
replaced or accepted; broad retrieval and Planner-quality evaluation remain separate work.
