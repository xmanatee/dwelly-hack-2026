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

Stage 3: the context model's case deadline now applies even with the offline Planner;
timeout retains the partial capture and model journal. Session activity is checked before
collection, before planning and before execution. The HTTP service rejects NaN/infinite
or nonpositive timeouts. Validation: 24 affected context/product/service tests, including
model cancellation and a disconnect between collection and planning; strict types.

## Final coverage and evidence

| Mechanism | Review / verification |
| --- | --- |
| Email / call / ticket intake | Existing vertical CLI tests retain the original route and exclude unrelated/future evidence. |
| Synthetic state and sources | Read-only, scoped decision-time snapshots, manifest guards and separate expected outcomes; existing dataset reused without regeneration. |
| Context collection | Source gaps, conflicting records, model journals and the newly enforced overall deadline. |
| Planner | Existing canonical decision schema, grounds, authority gate, repairs and shared product/Winner imports; no skill/model policy changed in this audit. |
| Execution and receipts | Ordering, replay conflicts, failure propagation and stopped sessions; bank actions remain simulated. |
| HTTP | Authentication, body/schema constraints, request serialization, replay, timeouts, closure and history tests. |
| Voice | Closed-session rejection, failed-result propagation, explicit simulated handoff status, safe source/state paths and the existing live queue seam. |
| Winner | Loader containment, generation/evaluation tests, exclusive output reservation and isolated workflow attempts. |
| Evaluation / reporting | Existing saved-result tests remain passing; baseline/reference and historical captures unchanged. |
| Setup / CI | Full lint/format/type/test gate; manual workflow YAML and shell syntax checked, not dispatched. |

Final full gate: **361 tests passed**, Ruff clean, strict mypy clean (172 source files).
After the full gate, the voice fixture's unsupported claim that an investigation was already
underway was replaced with “An investigation is still needed”; its voice tests were rerun.

Local checks without provider calls:

```sh
uv run dwelly-bot local run --case SYN-0001 --channel call \
  --state .cache/component-reaudit/local-receipts.sqlite \
  --output .cache/component-reaudit/local
uv run dwelly-bot voice ask --scope voice-demo-transfer \
  --records examples/voice/records.json --plan examples/voice/plan.json \
  --request 'Has my transfer arrived?' --output .cache/component-reaudit/voice
```

Both completed: local execution returned `simulated`; voice returned `answered` with
`handoff_status: simulated` and no unsupported completed-investigation claim. Local captures
remain under `.cache/component-reaudit/`. Use fresh paths to repeat.

Remaining product boundaries are unchanged: canonical-plan speech rendering, real banking
adapters, complete temporal entity state and OCR are not implemented. The fixture speech
queue does not make a handoff real. No live speech session or paid quality benchmark was run;
passing these checks is not a claim that arbitrary banking cases are solved correctly.
