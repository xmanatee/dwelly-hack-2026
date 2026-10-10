# Context gathering

`ContextCollector` produces the exact Markdown passed to Planner. There are two modes:

- Default: read configured sources once, without a model.
- `investigator=AgentInvestigator(budgeted_model, config)`: a small Pydantic AI agent
  identifies useful information, calls `read_source(source, question)` and follows up
  with more focused questions. It uses the existing CaseRuntime, model pool/budget
  wrapper and Journal. Model traces and accounting are local; instrumentation is off.

The agent outputs retrieval objectives and gaps. Evidence is assembled from the actual
source results, not from its paraphrase. Scope/time filtering happens **before** a source
response reaches the model. The model cannot choose another scope, database or file path.
No bank actions or final case decisions are exposed to this component.

## Plugging in Nikita's data

Implement `ContextSource.lookup(ContextQuery) -> SourceResult`. The query includes the
original request or focused question, IdentityHints, trusted scope, time cutoff and limit.
Return records with IDs, source, availability time, kind and text. Keep source facts intact.
Source names must be unique; their class docstrings describe their contents to the agent.

`JsonSource(path)` reads normalized JSON records. `SQLiteSource(path, table=...)` opens a
real database read-only and searches a configured table/view with these columns:
`id, scope_id, available_at, kind, source, text`. Times must be valid ISO 8601 with a zone.
Use a projection/view or adapter to map the actual customer/account/payment schema once
the files arrive. No arbitrary SQL is exposed to the model. Literal term matching is a
starting point, not semantic retrieval or identity verification.

The main missing production integration is the **source-specific join and access map**:
which customer, account, company and history records this authenticated request may read.
Do not broaden scope based on an email/name in message text. Ambiguous names should produce
separate candidate records and an explicit warning. Current fixtures already have case
membership; they do not solve cross-table identity resolution.

Still needed with the real files: schema mapping, document/media readers if present,
pagination for large histories, and tests against actual entity links. A lookup failure
is reported as a gap, never as “no matching customer.” Model-driven selection has offline
tool-loop coverage but has not yet been evaluated with a live model on these data.
