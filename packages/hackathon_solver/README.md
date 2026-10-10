# Hackathon Solver

Separate package from [the target architecture](../../docs/architecture/README.md): contest case → visible context → shared `dwelly_bot.planning` Planner → answer generator → `ANSWER.md` and `REASONING.md`. The product package does not depend on it.

Implemented so far: **generation** (Plan → answer/reasoning) and **export** (the two files per case). Case adapters, the runner and evaluation are not in this package yet.

```sh
uv run hackathon-solver generate --input DIR --output review/NAME --development
uv run hackathon-solver generate --input DIR --output review/NAME --development --config configs/planner-claude-code.json
```

- Input `DIR` holds `<case>.plan.json` (a shared `Plan`) and `<case>.context.md` (the visible decision-point text) per case.
- Without `--config`, `TemplateGenerator` renders the plan deterministically; it is the faithfulness reference. With `--config`, `ModelGenerator` makes one model call per case through the shared model pool or the Claude Code CLI, charged to the config's ledger.
- The plan is the decision of record: the generator never changes the decision, disposition or actions. Nothing is executed on this path, so a reply that reports a planned action as done is sent back for one repair. An insufficient plan is reported in the reasoning, not silently re-planned.
- Each case folder also gets `generation.json` with the plan, the generator input and output, for audit and for evaluating generation separately from planning.
- `--development` refuses an `ANSWERS` destination for practice cases; existing answers are never overwritten.
