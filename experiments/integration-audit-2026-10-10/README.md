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
