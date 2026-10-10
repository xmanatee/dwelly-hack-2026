# Components and integration

[Architecture](README.md) · [Checks and live captures](../../experiments/usability-integration/README.md)

The Planner is the shared decision core: context adapters supply evidence, it chooses a
concrete strategy, and each consuming application presents or executes the resulting plan.
The hackathon exercises this core directly through Winner.

| Component | Capability | Operating profile |
| --- | --- | --- |
| Intake | Typed email, call and ticket; original reply route; authenticated HTTP turns bound to a trusted session | Real email/ticket provider webhooks and their signature verification are deployment adapters. |
| Context | Read-only investigator, JSON/SQLite and synthetic-bank sources, scoped/time-filtered records, source errors and exact `context.md` | Trusted scope and reviewed decision-time snapshots; final challenge preparation adds PDF text and local image OCR sidecars. |
| Planner | Shared canonical `Plan`, skill selection, concrete decisions and evidence-linked grounds; product `DecisionPlanner` and Winner `make_plan` | Configurable model, versioned skills, structured decisions and preserved evidence. |
| Execution | Canonical `DecisionExecutor`, dependency validation, durable mock receipts, replay/conflict checks, original-channel routing and session closure guard | Canonical-plan effects remain simulated; the separate fixture voice path can queue speech. Live bank adapters need provider authority, idempotency and reconciliation. |
| Voice / text service | FastAPI/Uvicorn, session-scoped bearer tokens, SQLite request state, one active turn, timeout/close handling and replay after restart | Webhook mode needs HTTPS and a lifecycle handler. The team also added a local ElevenLabs WebSocket client-tool bridge with fixture speech; audio interruption/latency still need verification. |
| Winner | Folder input, supplied context and attachments, shared Planner, ANSWER/REASONING, labeled future drafts, failures and journals | Development histories need a decision-time projection; released challenges use all supplied evidence. Thirty final banking outputs are saved; completion is not a correctness score. |
| Storage | Dataset state, incoming cases and private evaluation material separated; source hashes; independent session and action-receipt SQLite | Local deployment only. Retention, backups and distributed locking depend on the deployment. |
| Evaluation | Saved-result scoring, public/synthetic preparation, model judge and existing report workflows | Historical scores are not a fresh quality baseline for this integrated product. |

## Shared decision contract

The product now accepts `--planner-config` and preserves the same complete decision schema
as Winner. The earlier offline fixture remains available without keys. HTTP intake invokes
that common pipeline rather than duplicating context/planning logic. Session history adds
customer assertions, never generated plans as bank facts. Closing a session while planning
prevents subsequent mock execution. Provider retries reuse persisted results.

Planner sees an explicit registry of valid evidence IDs; ambiguous input IDs are rejected.
Winner separates conditional future message drafts from current status and labels them
NOT SENT. Its generator repairs unknown prerequisite IDs and unsupported completion claims;
these guards are not a semantic correctness proof.

The team's [local voice bridge](../../examples/voice/README.md) is a second transport:
`voice ask` works offline, while `voice call` uses the ElevenLabs SDK. It queues the
fixture planner's `reply_to_trigger` in an open call; all other operations remain mock.
The HTTP service provides the model-backed path; the client-tool bridge provides the
prepared voice demonstration. [Choose a presentation profile](../../demo/LIVE-DEMO.md).

## Synthetic data boundaries

The current bank world has 1,180 cases and a reviewed decision-time projection. Full histories,
expected answers and final entity tables are separate. The runtime admits reviewed read
responses; command, mixed and unknown responses are withheld. Names, phone/email aliases and
claims in incoming messages are search hints, not identity verification. PDF text is extracted
when preparing the world; unavailable or unread attachments remain explicit gaps.

[Dataset setup and provenance](../../local_testing/banking/README.md) ·
[Context integration evidence](../../experiments/synthetic-context-integration/README.md)

## Before live deployment

Connect actual authorized source/action adapters, provision the speech provider and secure
HTTPS service, and test disconnects and uncertain provider outcomes. A SQLite mock receipt
cannot establish exactly-once behavior in an external bank. Do not tell a customer an operation
completed without a provider acknowledgement. Local captures contain request/model text;
choose access and retention appropriate to the deployment. No audio recording or vendor
telemetry is enabled by this repository.
