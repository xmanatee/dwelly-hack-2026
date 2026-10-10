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
