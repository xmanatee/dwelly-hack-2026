# Planner

Decision-point context in; **decided next actions with public grounds** out. The Planner has no tools. The solver/Winner preserves its decision; a contradictory new fact or failed execution gate blocks the affected action and requires a fresh decision. A plan is not proof that anything was executed.

```
case evidence → PlanInput → select skills → planner + selected knowledge → Plan → solver / Winner
```

- `contracts.py`: `PlanInput` (request, timed events, documents, datapoints, `solver_tools`) and `Plan` (facts with evidence IDs, identity/authority, safety flags, ordered steps, response guidance, expected disposition).
- `context.py`: builds `PlanInput` from the adapter's decision-point documents and the solver's own tool bindings, so disabled tools never appear.
- `validate.py`: steps must use listed solver tools or playbook actions; facts must cite input evidence; safety flags force their required actions; new decisions cannot schedule a state change behind an uncompleted identity check. A failed check uses the configured repair limit.
- `prompt.md`, `evidence.md`, `safety.md`: always-loaded instructions.
- [skills/](skills/README.md): eleven focused banking skills, an allowlisted catalog and official sources. `skills.py` selects relevant IDs with a separate structured model call, then loads their Markdown into the Planner.
- `playbooks/<name>.md|.json`: domain scope and the unchanged action/safety vocabulary.

The existing config value `mode: "advisory"` is retained for compatibility; it now means use the Planner’s decision of record.

Enable it in a run config; omit `model` to reuse the solver's model and account:

```json
{"planner": {"mode": "advisory", "playbook": "banking", "skill_selection": "model", "model": {"model": "claude-sonnet-5-5", "provider": "anthropic", "input_price_per_million": 3, "output_price_per_million": 15}}}
```

Selection uses the same Planner model and cumulative runtime limits, normally adding one call. Journals retain selected IDs, content hashes and both model calls. `skill_selection: "all"` is a preload mode for controlled comparisons; selection errors remain visible Planner failures. Common evidence and safety rules apply even with zero selected topics.

Plans are saved in each case's `state_snapshots.after.plan` with planner model calls under `model_roles`. A planner error is recorded and the solver runs without a plan. Turning the planner on changes agent behaviour, so compare it against the baseline through the experiment workflow.

Tune the planner alone, without running the solver:

```sh
uv run dwelly-bot plan --dataset dwelly-banking --dataset-root .cache/datasets/banking-v1 --config configs/planner-claude-code.json --output analysis/artifacts/plans-NAME
uv run dwelly-bot plan --input case.input.json --config configs/planner-claude-code.json --output analysis/artifacts/plans-NAME
```

`--inputs-only` writes the `PlanInput` JSON without model calls. `configs/planner-claude-code.json` runs the planner through the logged-in `claude` CLI; its ledger records API-equivalent prices as a usage guard.


## What a returned step means

`summary` is the selected decision. Each step contains:

| Field | Meaning |
| --- | --- |
| `action` | Operation from the allowed vocabulary |
| `instruction` | Concrete work, case details and recipient/message |
| `rationale.explanation` | Why this operation was selected |
| `rationale.evidence` | Actual input event/document IDs |
| `rationale.criterion` | The observed condition and applicable handling rule |
| `rationale.source` | Loaded `skill:<id>`, supplied `evidence:<id>`, or `general:planner`, `general:evidence`, `general:safety` |
| `requires` | Ordering between already-decided operations; never assumed consent or authority |

For example, a disclosed unsafe contact situation can lead to `refer_specialist`, with
an instruction naming the support role and safe-contact restriction, and grounds linking
the customer's disclosure to `skill:financial-abuse`. A support need alone is not an
automatic legal requirement to hand off: the rule and observed criterion must explain
this particular decision. A named skill is guidance, not a fabricated statute citation.

Live `make_plan` requires grounds for every step and validates evidence/rule references.
It rejects free-form future `condition`/`escalate_if` branches and read-only non-decisions.
Missing essential facts lead to a specific request or handoff now; future customer answers
can trigger a new plan. Validation checks structure/references, not the truth of every
natural-language explanation; semantic review and evaluation remain necessary.

Historical captures with `purpose` still load into `instruction`; absent historical
rationales remain `null`, never fabricated. `check_plan` defaults to historical-compatible
checks; `make_plan` always enables `require_decision=True` and supplies loaded skill IDs.
The legacy `proposed_action` type name means decided work awaiting execution, not an
invitation for the next agent to reconsider it. Winner keeps these grounds in REASONING.md
and displays them alongside each action in its HTML report.

## Evaluate plans

```sh
uv run --extra analysis dwelly-bot plan eval build --cases "dwelly-cases/Banking & Financial Services" --output analysis/artifacts/plan-eval/public
uv run --extra analysis dwelly-bot plan eval build --cases "experiments/safety-cases/Banking & Financial Services" --labels experiments/safety-cases/labels.json --prefix safety --attachments --output analysis/artifacts/plan-eval/safety
uv run dwelly-bot plan --input analysis/artifacts/plan-eval/public/inputs --config configs/planner-claude-code.json --output analysis/artifacts/plan-eval/public-plans
uv run dwelly-bot plan eval score --references analysis/artifacts/plan-eval/public/references.json --plans analysis/artifacts/plan-eval/public-plans --output analysis/artifacts/plan-eval/public-score.json
```

- `build` cuts each case's history.md before every bank-agent event (`history_view`; index.md is never read), and builds inputs through `BankingSession.plan_input`, exactly as at run time. With `--labels`, it cuts only at each labelled decision event. `--attachments` adds attachment text; the public cases withhold attachments because their availability time is unknown.
- `references.json` holds the bank's actual next event, its heuristic action label, and expected safety flags with their required actions. It is never part of planner input. Review and correct `reference_action` labels by hand; scoring reads the file as given.
- `score` reports plan availability, next-action accuracy (first substantive proposed action, skipping identity confirmation), whether the reference action appears anywhere in the plan, safety-flag recall, required-action completeness, false flags on control cases, and flags raised on unlabelled cases. The recorded next event is one acceptable action, not the only correct one, so read the confusion pairs before drawing conclusions.

Synthetic cases from `synthetic/` use their own labels: first action and target, required gates, must-not, must-convey, unsupported claims and signposts. `--per-scenario N` takes the first N cases of each of the 75 scenarios. The planner sees the events up to the labelled decision point, the attachments available by then and the synthetic bank's systems catalogue (`datapoints.bank_systems`). `--records` also adds lookup-style system responses as `records/` documents; the same reviewed query allowlist as the local banking adapter admits observations and withholds command, mixed and unknown responses. System kind or action-word matching alone is not sufficient. `score` then also reports `target_match` against the labelled target system.

```sh
uv run --extra analysis dwelly-bot plan eval build --synthetic .cache/datasets/banking-synth --per-scenario 2 --output analysis/artifacts/plan-eval/synthetic
```

Standalone Planner runs save configuration, model messages and cost receipts in each local journal, including failed calls, and return a nonzero exit code when any plan fails.
