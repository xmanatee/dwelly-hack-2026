# Hackathon Solver

Separate package from [the target architecture](../../docs/architecture/README.md): contest case → visible context → shared `dwelly_bot.planning` Planner → answer generator → `ANSWER.md` and `REASONING.md`. The product package does not depend on it.

Implemented so far: **generation** (Plan → answer/reasoning), **export** (the two files per case) and a development **predict** run. Contest adapters and evaluation are not in this package yet.

```sh
uv run hackathon-solver generate --input DIR --output review/NAME --development
uv run hackathon-solver generate --input DIR --output review/NAME --development --config configs/planner-claude-code.json
```

- Input `DIR` holds `<case>.plan.json` (a shared `Plan`) and `<case>.context.md` (the visible decision-point text) per case.
- Without `--config`, `TemplateGenerator` renders the plan deterministically; it is the faithfulness reference. With `--config`, `ModelGenerator` uses the shared `CaseRuntime`, model pool or Claude Code CLI and budget ledger. Request/token limits and configured repair attempts apply; model messages, configuration and costs are saved in local journals.
- The plan is the decision of record: the model generator is instructed to preserve its decision, disposition and actions. This is not a semantic proof of faithfulness; inspect generated answers. Nothing is executed on this path, so a reply that reports a planned action as done is sent back within the configured repair limit. An insufficient plan is reported in the reasoning, not silently re-planned.
- Each case folder also gets `generation.json` with the plan, the generator input and output, for audit and for evaluating generation separately from planning.
- `--development` refuses an `ANSWERS` destination for practice cases; existing answers are never overwritten.

## Predict development cases

```sh
uv run hackathon-solver predict --config configs/planner-claude-code.json
```

For each case: its full `history.md` (all events; `index.md` and other case files are never read) → `dwelly_bot.planner` case planner → generator → files. `--cases` is a track folder of `NNN/history.md`, by default the installed public originals. Results go to ignored `experiments/banking-predictions/artifacts/<UTC stamp>/` unless `--output` is given: `<case>/ANSWER.md`, `<case>/REASONING.md`, `<case>/generation.json` (plan, visible context, generator details), `predictions.json` (status, requests, cost per case), `journals/` and `report.html` (searchable page of all cases; rebuild with `hackathon-solver report --input DIR`). Public practice cases are refused in `ANSWERS`. A Planner or generator failure still writes both files as a human-review notice, preserves the trace, continues other cases and causes a nonzero command exit. `predict` shares request/token usage across both roles and honors `planner.model` when set. `--template` uses the deterministic generator; `--ids` selects cases. The case planner's plan is its own schema until it moves to the shared `text → Plan` contract.

Full-history predictions include every event in the supplied history. They are retrospective development outputs, not a blind decision-point evaluation. Use the evaluation adapter and its cutoff for benchmark claims. The installed public practice corpus cannot be selected with `--submission`.
