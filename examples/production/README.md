# Offline production skeleton

These are newly authored fixtures, not copied banking cases or Nikita's database schema.
They exercise the same pipeline through email, a live call and an assigned ticket.

From the repository root:

```sh
uv run dwelly-bot demo --input examples/production/email.json --records examples/production/records.json --output .cache/production-demo/email
uv run dwelly-bot demo --input examples/production/call.json --records examples/production/records.json --output .cache/production-demo/call
uv run dwelly-bot demo --input examples/production/ticket.json --records examples/production/records.json --output .cache/production-demo/ticket
```

Each output directory must be new. The command does not load credentials, initialize an
LLM, use the network, or perform external actions. Existing outputs are never overwritten.

## Components to replace

| Component | Current implementation | Integration point |
| --- | --- | --- |
| Intake | Typed `EmailInput`, `CallInput`, `TicketInput` → `Trigger` | A real transport adapter supplies event ID, timestamp, trusted case scope and reply route. |
| Hint extraction | Literal email/reference parsing; supplied name/ID/phone hints | `HintExtractor.extract(text, supplied)` can use a lightweight model later. Names are unverified hints. |
| Context sources | `InMemorySource`, filtered by case scope and availability time | `ContextSource.lookup(ContextQuery)` can search Nikita's DB, histories and documents using hints. The source owns entity resolution and access checks. |
| Collection | `ContextCollector.collect(...)` → text and provenance | `CollectedContext.write(path)` saves the exact `context.md` passed to Planner. |
| Planning | `HumanReviewPlanner`, no skills or model | Vera replaces `Planner.plan(context: str) -> Plan`. |
| Execution | `MockExecutor` | `execute(trigger, plan, journal)` resolves actions and returns explicit mock receipts. |
| Orchestration | `ProductionPipeline.run(event, output)` | All three channels await this same method; no second delivery stage runs after it. |

The source interface is deliberately small. The fixture source already has case membership;
it does **not** discover cross-table relationships, fuzzy-match customers or verify identity.
There is no lightweight LLM parser yet. Sources may return warnings about ambiguity or
partial data; failures remain visible in the collected text. Facts are sorted by their
availability time and preserve their source IDs. Original message text is retained.

`scope_id` is an authorized case/access boundary supplied by integration code, not a value
to trust from a public webhook body. Matching names cannot expand that boundary. Real
sources must enforce appropriate record-level permissions as well as time bounds.

## Plans and completion

The placeholder always emits `handoff(human-support)` followed by `reply_to_trigger`.
The latter resolves to an email reply in the same thread, speech in the current call, or
a ticket comment. An inactive call fails; it does not silently become an outbound call.

Other explicit categories are `send_email`, `call_customer` and `update_ticket`.
Updating or closing a ticket is an action; it is not an automatic side effect of returning
a result. The mock accepts these categories but contains no bank or messaging connectors.
It records intent/parameters and simulation receipts, not a working ticket database.

Actions run in order. A failure skips remaining actions. There is no business re-planning
inside the executor. `result.json` has `mode: mock` and receipt states `simulated`, `failed`
or `skipped`; it never asserts a real handoff or delivery. Empty plans have status `empty`.

Replay protection uses scope + event ID + action ID, rejects changed input under the same
key, and lasts only as long as that `MockExecutor` instance. CLI invocations create fresh
instances. Durable replay protection, real permissions, live call lifecycle events,
retries/recovery and actual adapters remain integration work, not production guarantees.

## Captures

- `input.json` and `trigger.json`: inbound event and normalized original route.
- `context.md`: the exact text sent to Planner; `context.json`: source records and warnings.
- `plan.json`: the chosen structured plan.
- `result.json`: action results, destinations and parameters, explicitly simulated.
- `events.jsonl`: the existing shared local Journal, with started/returned/error events.
- `failure.json`: incomplete pipeline receipt when an exception interrupts a stage.

The fixture includes one future record and one record for another case with the same name.
Neither appears in the 10:00 context. No contest answer/outcome is loaded by this demo.
Separate Hackathon Solver packaging and answer generation remain the next integration.
