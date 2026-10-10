# Usable component integration

Work proceeds in independently validated, synchronized commits. Initial offline gate:
335 tests passed, Ruff and strict types passed. The saved agent baseline is stale;
its reference and execution captures remain unchanged. These are integration changes,
not adoption of a new quality baseline or a claim of improved banking decisions.

| Stage | Mechanism | Implementation / validation |
| --- | --- | --- |
| 0 | Team state | Preserve the existing local report; integrate the team's dashboard before changes |
| 1 | Shared decision core | Connect local context to the same Planner imported by Winner; preserve its full decision schema and use an explicit mock executor for that schema |
| 2 | Voice / HTTP intake | Optional authenticated service, trusted session-to-case binding, durable request state, replay/conflict handling, ElevenLabs server-tool contract |
| 3 | Winner / evidence contracts | Inspect canonical evidence, output and failure handling; correct concrete integration defects without changing historical captures |
| 4 | Usability | Update obsolete ownership/setup claims, run affected integration checks and full offline gate, exercise local commands |

Keep the offline human-review demo available. A configured model run must explicitly
select the model, preserve traces and use the shared pool/ledger. No mock receipt is
a real bank operation. External bank/ticket/email credentials and provider provisioning
are deployment inputs, not facts that can be invented by this repository.

Research uses primary provider/framework documentation. No telemetry, vendor session
capture, audio recording or outbound customer communication is enabled by this work.

## Stage 1 evidence

`demo` and `local run` accept `--planner-config`; it is mutually exclusive with a
fixture `--plan`. `DecisionPlanner` invokes the existing skill selector and `make_plan`,
with shared provider/ledger and a preserved `planner.jsonl`. `ProductionPipeline`
is typed over its plan schema; canonical case plans do not lose grounds/dependencies
through a conversion to the old six-action fixture contract. `DecisionExecutor`
validates operation ordering and simulates the canonical actions with durable receipts.
Replies bind to the incoming route; inactive calls fail without an automatic callback.
The original offline fixture pipeline remains available.

Validation: 29 affected tests passed (including two new integration tests), Ruff and
strict types. FunctionModel tests exercise the real shared Planner orchestration,
not banking answer quality. No paid model run or baseline adoption in this stage.

```sh
uv run dwelly-bot demo --input examples/production/call.json \
  --records examples/production/records.json \
  --planner-config src/hackathon_winner/config.json \
  --output .cache/product/model-call
```

## Stage 2 evidence

Optional FastAPI/Uvicorn service with CLI-provisioned session bindings, bearer authentication,
SQLite request claims/results, same-input replay after restart, serialized turns, timeouts,
closed-session checks and bounded incoming text. It invokes the common product harness and
adds previous customer assertions without promoting model output to bank evidence. A closed
session invalidates execution after planning. ElevenLabs webhook setup is documented against
primary documentation; no vendor account resources or recordings are created.

The server extra is optional for users; the full CI gate now installs all extras. Offline
ASGI tests cover auth/scope, replay/conflict, timeout, pipeline captures/history and disconnect.
A live provider audio conversation still requires account provisioning and has not been run.

## Stage 3 evidence

Planner receives an explicit canonical evidence-ID registry, including document-only inputs;
repair feedback repeats the allowed IDs. Ambiguous duplicate/reserved evidence IDs fail at
the input boundary. Winner's TASK now agrees with the concrete-next-action contract, and case
folder names cannot collide with output metadata. No organizer/source bytes were rewritten.

Generator future-message drafts have a separate typed field with existing plan-step
prerequisites. Export labels each draft NOT SENT and requires confirmed execution first;
ordinary answer/reasoning still reject first-person claims that planned work was performed.
Unknown draft prerequisites are repaired. This addresses the future-draft false positive
without silently treating a planned operation as a receipt. The regex is a narrow guard,
not proof of semantic faithfulness in every language; saved-result judging remains separate.

## Stage 4: verified local operation

At source commit `e71c742`, the full offline gate passed: **344 tests**, Ruff and strict
mypy (167 source files). Paid integration smokes then completed with no run errors:

| Path | Input | Inspected result |
| --- | --- | --- |
| Model collector → shared Planner → mock executor | Existing synthetic `SYN-0001`, call replay | Fee review / complaint request and response bound to the original call; both receipts simulated. |
| Winner → shared Planner → generator | Bundled synthetic `001` | Hold unauthenticated contact change and route to secure recovery; no completed update claimed. |
| Winner → shared Planner → generator | Bundled synthetic `002` | Preserve the distinction between sent and credited; no unsupported recall or duplicate payment. |

Commands (use fresh output directories):

```sh
uv run dwelly-bot local run --case SYN-0001 --channel call \
  --context-config experiments/synthetic-context-integration/config.json \
  --planner-config src/hackathon_winner/config.json \
  --output experiments/usability-integration/artifacts/live-local-e71c742
uv run hackathon-winner --config src/hackathon_winner/config.json \
  --output experiments/usability-integration/artifacts/winner-e71c742
```

The 11 model requests have a configured-price upper bound of **$0.1785604**, including
context collection, skill selection, planning and answer generation. This is not a provider
invoice. These three inspected inputs establish integration only, not corpus-wide decision
quality, absence of overfitting or an accepted baseline. The old baseline remains stale.

A real local Uvicorn process was also exercised without models: health 200, missing bearer
401, turn 200, identical replay 200 with a replay header, close 200, new turn after close 410.
It was stopped after the check. The first smoke harness attempted unsupported
`python -m dwelly_bot`; it was corrected to the documented `dwelly-bot` entry point before
any request ran. HTTP session credentials, state database and logs are excluded from export.

[Winner HTML report](report.html) · [Verification and file hashes](verification.json) ·
[Unmodified captures, compressed](captures.tar.gz)

Documentation now points to the implemented shared Planner and authenticated service.
[Component inventory](../../docs/architecture/integration-status.md) distinguishes working
local mechanisms from real banking adapters, provider audio deployment and other remaining
capabilities. No external bank operation, outbound message or live ElevenLabs audio session
was performed. No baseline reference or historical run was rewritten.

## Team synchronization follow-up

The team changed the default Winner model to Fable 5.1 and added wrapped-folder loading
(`c729639`), then added a manual workflow (`f6e0833`). Both were integrated. Wrapped-folder
traversal now retains the original source containment check, with a regression test for
outside symlinks, ordinary wrappers, decoding and explicit IDs (23 affected tests passed).

A repeated local call correctly failed with an idempotency conflict because a different
model proposed changed actions for the same event in the existing receipt database. A fresh
experiment must use a separate `--state`; do not disable replay protection. The failed capture
is retained. A new local run uses an independent experiment state.

The Fable Winner smoke exposed a repair problem: a verification referral was encoded as
`request_team_action`, whose vocabulary category is state-changing. Repair only reworded the
instruction and repeated the forbidden category. The authority gate remains unchanged.
The general prompt and repair feedback now explain that category explicitly and distinguish
verification/support referrals from authorized operations. This is a contract clarification,
not a scenario-specific answer or adoption of a new quality baseline.
