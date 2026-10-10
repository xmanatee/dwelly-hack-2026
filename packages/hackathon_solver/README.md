# Hackathon Solver

Separate package from [the target architecture](../../docs/architecture/README.md): contest case → visible context → shared `dwelly_bot.planning` Planner → answer generator → `ANSWER.md` and `REASONING.md`. The product package does not depend on it.

Implemented so far: **generation** (Plan → answer/reasoning), **export** (the two files per case) and a development **predict** run. Contest adapters and evaluation are not in this package yet.

```sh
uv run hackathon-solver generate --input DIR --output review/NAME --development
uv run hackathon-solver generate --input DIR --output review/NAME --development --config configs/planner-claude-code.json
```

- Input `DIR` holds `<case>.plan.json` (a shared `Plan`) and `<case>.context.md` (the visible decision-point text) per case.
- Without `--config`, `TemplateGenerator` renders the plan deterministically; it is the faithfulness reference. With `--config`, `ModelGenerator` makes one model call per case through the shared model pool or the Claude Code CLI, charged to the config's ledger.
- The plan is the decision of record: the generator never changes the decision, disposition or actions. Nothing is executed on this path, so a reply that reports a planned action as done is sent back for one repair. An insufficient plan is reported in the reasoning, not silently re-planned.
- Each case folder also gets `generation.json` with the plan, the generator input and output, for audit and for evaluating generation separately from planning.
- `--development` refuses an `ANSWERS` destination for practice cases; existing answers are never overwritten.

## Predict development cases

```sh
uv run hackathon-solver predict --dataset-root .cache/datasets/banking-v1 --config configs/planner-claude-code.json
```

For each case at its decision point: visible evidence → `dwelly_bot.planner` case planner → generator → files. Results go to ignored `experiments/banking-predictions/artifacts/<UTC stamp>/` unless `--output` is given: `<case>/ANSWER.md`, `<case>/REASONING.md`, `<case>/generation.json` (plan, visible context, generator details), `predictions.json` (status, requests, cost per case), `journals/` and `report.html` (searchable page of all cases; rebuild with `hackathon-solver report --input DIR`). Public practice cases are refused in `ANSWERS`. A planner failure still writes both files, as a human-review notice with the error. `--template` uses the deterministic generator; `--ids` selects cases. The case planner's plan is its own schema until it moves to the shared `text → Plan` contract.
