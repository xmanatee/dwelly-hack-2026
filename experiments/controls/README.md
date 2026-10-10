# Required case controls — prototype

- Configured questions → cited yes/no/unknown observations → prescribed handling → guarded tools. The acting agent cannot skip the checkpoint, replace questions or approve an operation.
- `questions.json` contains draft scenario checks, not adopted legal/compliance policy. `dwelly_bot.harness.control_checks` reuses the common model, budget, journal and reports.

```python
gate = ControlChecklist(questions, parent=runtime.policy_gate)
runtime.policy_gate = gate
controls = await gate.assess(runtime, sources)
```

- Install after domain guards; retain the parent. Coordinator updates context at intake and after new evidence. Changed context invalidates old answers; failed/stale/incomplete checks cannot clear a hold.
- Every question is required. Exact quotes establish provenance, not truth/entailment; classifier false negatives remain possible. Policy-role checker has no business tools.
- `adapt` guides support; `clarify`, `human_review`, `deny` describe routing. Explicit blocked tool names cover writes and sensitive reads; keep retrieval/clarification/handover available.
- Connector checks retain authority over identity, recipient, lawful basis and exact-action approvals. Model observations, skills and retrieved policies never grant permissions; independent verification checks actual effects.
- Saturday determines jurisdiction, approved policy/version/scope, questions, authoritative facts, tools, approval transport and handover/resume bindings. Record practical needs/minimum evidence, not inferred diagnoses or private transcripts.

## Scope

- Retained for future operational adapters; Read-only banking cases do not use this checkpoint.
- Sources: [FCA support needs](https://www.fca.org.uk/publications/finalised-guidance/guidance-firms-fair-treatment-vulnerable-customers), [ICO data categories](https://ico.org.uk/for-organisations/uk-gdpr-guidance-and-resources/lawful-basis/special-category-data/what-is-special-category-data/), [customer due diligence](https://www.legislation.gov.uk/uksi/2017/692/regulation/28), [Pydantic deferred tools](https://pydantic.dev/docs/ai/tools-toolsets/deferred-tools/).

## Offline verification

```sh
uv run dwelly-bot check
uv run python experiments/controls/demo.py --output experiments/controls/artifacts/offline-001
```

- Scripted synthetic demo, not live model-quality/compliance evidence. Tests cover skipped/stale checks, unknown/unsupported answers, sensitive reads, parent guards and classifier failure.
