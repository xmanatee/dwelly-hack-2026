# Banking source analysis

Use [analyze](../.agents/skills/analyze/SKILL.md) and its [playbook](../.agents/skills/analyze/references/playbook.md) to choose methods for a concrete question. The default recipe counts development cases and visible event channels, and makes the initial requests inspectable. Its unit is one case, except channel counts, which count events.

```sh
uv run --extra analysis dwelly-bot analyze run dwelly_bot.analysis.banking --data dataset
uv run --extra analysis dwelly-bot analyze report --input analysis/artifacts/RUN/analysis.json --output analysis/artifacts/RUN/analysis.html
```

The recipe reads only `cases.json` and `documents/`; originals, later history, attachments and outcomes are excluded. It uses no paid models by default. Shared helpers support profiling, sample review, text groups, semantic maps, quoted evidence extraction and optional model discovery. Use `configs/analysis.toml` only for explicitly requested paid work; it shares the cumulative Anthropic ledger. Source observations, model interpretations and verified operational effects remain distinct.

Recipes expose `build(ctx) -> Report`. Keep dataset semantics in the recipe and reusable methods under `src/dwelly_bot/analysis/`. Reports contain source hashes, sample counts and limitations; generated HTML/JSON stay ignored under `analysis/artifacts/`. Pages builds only offline source analysis and saved execution reports. Analysis findings may change the agent only through the experiment workflow.
