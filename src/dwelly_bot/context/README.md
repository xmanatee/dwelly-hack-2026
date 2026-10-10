# Context gathering

`ContextCollector` writes the exact Markdown passed to Planner. Two modes share its contract:

- Default: read configured sources once, without a model.
- `AgentInvestigator(budgeted_model, config)`: Pydantic AI identifies information needs,
  selects `read_source(source, question)` calls and follows references. The common
  CaseRuntime, provider pool, budget and local journal remain in use.

The Planner receives **observed source records, actual read questions and source warnings**.
Free-form model notes are recorded as `context_research_notes` in the journal; they are
not inserted into Planner evidence. Live smoke testing showed why: an investigator can
mistake a transport alias for a registered number, or missing simulator data for a negative
bank finding. Keeping those interpretations separate makes the evidence boundary explicit.

Scope/time filtering runs before records reach the model. No bank actions, arbitrary SQL,
evaluator labels or final case decisions are exposed to this component.

## Synthetic bank integration

[Build and run](../../../local_testing/banking/README.md) ·
[Adapter](../adapters/synthetic_banking/sources.py) ·
[Saved integration checks](../../../experiments/synthetic-context-integration/README.md)

The adapter supplies a scoped contact directory, visible case threads, extracted attachments
and 32 named bank-system interfaces. Twenty-eight have retained read-response types in the
current corpus. A reviewed query allowlist removes command outputs and mixed/unreviewed
responses. The original entity tables describe final state and stay outside runtime access.

Exact name, email and phone searches return candidates within the trusted scenario scope.
Ambiguous names remain separate. `.invalid` emails and `+999` phone numbers are generated
local routing aliases, not registered bank details or authentication. JSON triggers are
trusted local inputs; a future public webhook must establish its own access boundary.

PDF text and plain text/CSV are prepared offline. PNG contents are explicitly unavailable.
No copied title, outcome, later event or evaluator answer enters the runtime database.

## Other sources

Implement `ContextSource.lookup(ContextQuery) -> SourceResult`. A query contains the original
request or a focused question, identity hints, trusted scope, cutoff and result limit.
Return source records with IDs, availability times and unmodified evidence text. Source
names are unique; their descriptions explain what the investigator may retrieve.

`JsonSource(path)` reads normalized records. `SQLiteSource(path, table=...)` searches a
configured read-only table/view with `id, scope_id, available_at, kind, source, text`.
Source-specific joins and access checks belong in adapters, never in Planner.

Remaining integration work: temporal entity versions, genuine registered contact data,
authorized cross-entity joins, pagination for larger histories and image reading. Three
live model smokes establish tool wiring, not general retrieval accuracy.
