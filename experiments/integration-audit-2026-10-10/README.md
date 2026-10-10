# Integration audit — 10 October 2026

This is implementation and offline regression evidence, not an accepted agent experiment.
The saved baseline predates the current runtime and fails the source-freshness check.
Its reference and captures are preserved; no quality improvement or baseline adoption is claimed.

## Context collection

Hypothesis: a failed database read should become an explicit source gap while successfully
retrieved evidence remains available. Both deterministic and model-directed collection now
use the same bounded read boundary. Caller cancellation still stops the run. The shared
runtime's overall tool/request limits remain in force.

Offline tests exercise a timed-out source, a failed source, cancellation and scope/time guards.
No prompts, model selection or historical captures were changed.

## Planner and Solver commands

Hypothesis: every model role must obey shared limits and leave an inspectable local trace;
a failed case must not look like a successful batch. Generation now uses `CaseRuntime`,
shares case usage with planning in `predict`, honors the configured planner model, and
saves messages/configuration/cost receipts on success or failure. Failed model cases keep
human-review notices and do not discard later cases; commands exit nonzero on failures.

Template conversion now handles calculations and preserves conditional steps, prerequisites
and `must_not` constraints. Empty corpora and unsafe/duplicate standalone Planner IDs fail
before output or model calls. Practice export checks cover nested `ANSWERS` directories.
Full-history reports explicitly describe their retrospective scope.

Offline function-model tests cover both failure stages, continuation, planner model selection,
request/token settings, traces, conditional rendering and command exit codes. These are
integration checks, not evidence that model-authored answers are always faithful.

The investigator's read boundary owns the source timeout and uses the smaller of the
collector timeout and configured tool limit. This avoids two equal deadlines racing:
the source can return a gap instead of the outer tool cancelling that conversion.
Other runtime tools keep their existing timeout handling.

## Synthetic data and local runner

The importer now builds in a temporary sibling and publishes only a complete projection.
It rejects recursive output and invalid case IDs, preserves timezone offsets as actual UTC
instants, and records incoming case file hashes in new manifests. Runtime checks validate
those hashes when present. Existing v1 captures and datasets remain readable unchanged;
older manifests without `cases_sha256` verify the runtime database but not trigger bytes.

Local replay rejects ambiguous contact routes and scope/filename mismatches. Receipt stores
cannot occupy the capture directory. Dataset provenance is written at pipeline start so an
execution failure still retains the exact dataset receipt and partial evidence.

Offline tests cover failed-import cleanup, timezone conversion, trigger tampering, malformed
manifests, ambiguous routes, conflicting paths and failure captures. Original generated
corpus bytes and historical run outputs were not regenerated or edited.

## Consistent evaluation evidence

The synthetic Planner evaluation builder previously used a separate action-word heuristic.
It now imports the adapter's reviewed observation policy. Unknown query types are withheld,
and reviewed observations are not dropped merely because their query mentions a change or
block. The source database opens read-only. A regression covers both cases. Existing saved
scores are not regenerated: changed input evidence needs a new evaluation before comparison.

## Verification receipts

[Local verification](local-verification.json) records three offline runs on the existing
seed-2026 data (ticket SYN-0001, call SYN-0250, email SYN-0813), with capture hashes and the
source commit. All produced source context, the human-review plan and two simulated effects.
Captures remain under the ignored `.cache/integration-audit-20261010/` directory. No paid
model jobs, external messages or bank actions were triggered during this audit.

Intentional remaining integration work: align the advisory and executable Planner contracts
with Vera, attach real channel/voice/bank adapters, add temporal entity snapshots/OCR, and
run a fresh accepted benchmark. The audit does not turn these placeholders into deployed
production functionality.

Final offline gate: `uv run dwelly-bot check` passed Ruff lint/format, strict mypy on
147 source files, and **302 tests**. The initial gate had 282 passing tests; the added
regressions exercise the failures above. `main` was fetched again before publication.
The pre-existing dirty `experiments/baseline/report.html` is outside this task's commits.
