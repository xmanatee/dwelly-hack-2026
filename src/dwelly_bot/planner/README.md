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
