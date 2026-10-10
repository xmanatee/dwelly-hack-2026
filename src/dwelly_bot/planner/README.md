# Planner

Decision-point context in, advisory solver plan out. The planner has no tools; the solver keeps its own instructions, policies and tool limits, and treats the plan as untrusted advice.

```
case evidence → PlanInput (JSON) → planner → Plan (JSON, code-checked) → solver
```

- `contracts.py`: `PlanInput` (request, timed events, documents, datapoints, `solver_tools`) and `Plan` (facts with evidence IDs, identity/authority, safety flags, ordered steps, response guidance, expected disposition).
- `context.py`: builds `PlanInput` from the adapter's decision-point documents and the solver's own tool bindings, so disabled tools never appear.
- `validate.py`: steps must use listed solver tools or playbook actions; facts must cite input evidence; safety flags force their required actions; state-changing actions need identity and authority first. A failed check gets one repair attempt.
- `prompt.md` and `playbooks/<name>.md|.json`: the tunable parts. The JSON defines the action vocabulary, state-changing and identity actions, and each safety flag's required actions.

Enable it in a run config; omit `model` to reuse the solver's model and account:

```json
{"planner": {"mode": "advisory", "playbook": "banking", "model": {"model": "claude-sonnet-5-5", "provider": "anthropic", "input_price_per_million": 3, "output_price_per_million": 15}}}
```

Plans are saved in each case's `state_snapshots.after.plan` with planner model calls under `model_roles`. A planner error is recorded and the solver runs without a plan. Turning the planner on changes agent behaviour, so compare it against the baseline through the experiment workflow.

Tune the planner alone, without running the solver:

```sh
uv run dwelly-bot plan --dataset dwelly-banking --dataset-root .cache/datasets/banking-v1 --config configs/planner-claude-code.json --output analysis/artifacts/plans-NAME
uv run dwelly-bot plan --input case.input.json --config configs/planner-claude-code.json --output analysis/artifacts/plans-NAME
```

`--inputs-only` writes the `PlanInput` JSON without model calls. `configs/planner-claude-code.json` runs the planner through the logged-in `claude` CLI; its ledger records API-equivalent prices as a usage guard.

## Evaluate plans

```sh
uv run --extra analysis dwelly-bot plan eval build --cases "dwelly-cases/Banking & Financial Services" --output analysis/artifacts/plan-eval/public
uv run --extra analysis dwelly-bot plan eval build --cases "experiments/safety-cases/Banking & Financial Services" --labels experiments/safety-cases/labels.json --prefix safety --attachments --output analysis/artifacts/plan-eval/safety
uv run dwelly-bot plan --input analysis/artifacts/plan-eval/public/inputs --config configs/planner-claude-code.json --output analysis/artifacts/plan-eval/public-plans
uv run dwelly-bot plan eval score --references analysis/artifacts/plan-eval/public/references.json --plans analysis/artifacts/plan-eval/public-plans --output analysis/artifacts/plan-eval/public-score.json
```

- `build` cuts each case before every bank-agent event with the adapter's `initial_view`, and builds inputs through `BankingSession.plan_input`, exactly as at run time. With `--labels`, it cuts only at each labelled decision event. `--attachments` adds attachment text; the public cases withhold attachments because their availability time is unknown.
- `references.json` holds the bank's actual next event, its heuristic action label, and expected safety flags with their required actions. It is never part of planner input. Review and correct `reference_action` labels by hand; scoring reads the file as given.
- `score` reports plan availability, next-action accuracy (first substantive proposed action, skipping identity confirmation), whether the reference action appears anywhere in the plan, safety-flag recall, required-action completeness, false flags on control cases, and flags raised on unlabelled cases. The recorded next event is one acceptable action, not the only correct one, so read the confusion pairs before drawing conclusions.

Synthetic cases from `synthetic/` use their own labels: first action and target, required gates, must-not, must-convey, unsupported claims and signposts. `--per-scenario N` takes the first N cases of each of the 75 scenarios. The planner sees the events up to the labelled decision point, the attachments available by then and the synthetic bank's systems catalogue (`datapoints.bank_systems`). `--records` also adds lookup-style system responses as `records/` documents; responses to action queries (blocks, registrations, changes) are never included because they describe effects after the decision. `score` then also reports `target_match` against the labelled target system.

```sh
uv run --extra analysis dwelly-bot plan eval build --synthetic .cache/datasets/banking-synth --per-scenario 2 --output analysis/artifacts/plan-eval/synthetic
```
