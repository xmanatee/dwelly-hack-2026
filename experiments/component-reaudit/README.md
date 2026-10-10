# Second component audit

Scope: intake, sources, context, Planner, executor, HTTP and voice sessions, Winner,
storage and CI. Preserve team work and original captures. No paid benchmark, baseline
acceptance, vendor provisioning or recordings are part of this audit.

The saved baseline remains stale; these are integration fixes and offline regression checks,
not a claim of better banking decisions.

| Stage | Finding / intended check |
| --- | --- |
| Voice | Reject closed sessions before work, preserve execution failure, label simulated handoffs, protect source databases from receipt writes, close the queue on provider disconnect. |
| Winner | Preserve complete per-run artifacts on failure/retry; avoid overwriting existing run metadata or disguising partial results as a complete run. |
| Common runtime | Check deadlines, evidence boundaries, session state and immutable captures; full offline gate after integration. |

The shared runtime now explicitly rejects a canonical Planner plus the fixture speech queue:
that combination has no speech renderer and must not silently return no speech. The HTTP
service remains the model-backed integration; the client-tool voice path retains fixture plans.

Stage 1 validation: 16 affected voice/product/service tests passed. Regressions cover
closed-call rejection, failed execution with queued speech, simulated handoff metadata and
source SQLite preservation. No provider session or model call was made.

Stage 2: Winner now exclusively reserves output before model calls; a concurrent-writer
regression preserves the submission README and permits exactly one writer. The manual
workflow saves attempts separately, uploads failed-run captures, publishes only successful
full snapshots to ANSWERS, and keeps partial runs with their own metadata. Git ref fetching
works for branches, tags and commit IDs without cloning over a partially created directory.
Validation: 24 Winner/evaluation tests, Ruff, strict mypy; workflow YAML and shell syntax
checked offline. The GitHub workflow itself was not dispatched.
