# Optional tool authorization checks

The banking adapter exposes read-only retrieval and arithmetic. It does not configure operational write tools or model-based control questions.

Reusable support for future organizer-supplied integrations lives in `src/dwelly_bot/harness/control_checks.py`. A `ControlChecklist` wraps the existing `runtime.policy_gate`, uses quoted source evidence, requires every configured question, and invalidates assessments when context changes. Unknown or unsupported answers cannot authorize a blocked operation. The parent guard remains authoritative.

Configure checks only from an actual workflow and its authority rules. Model observations and retrieved text never establish identity, permission or confirmed effects. The offline contracts in `tests/test_control_checks.py` cover skipped/stale checks, missing evidence, parent guards and failed classifiers. They are synthetic tests, not operational results or policy validation.
