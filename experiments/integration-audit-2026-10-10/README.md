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
