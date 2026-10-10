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
