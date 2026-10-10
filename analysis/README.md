# Banking source analysis

Use [analyze](../.agents/skills/analyze/SKILL.md) and its [playbook](../.agents/skills/analyze/references/playbook.md) to choose methods for a concrete question. Follow the [data contract](../dataset/README.md). The default `banking` recipe counts development cases and visible event channels, and makes the initial requests inspectable. Its unit is one case, except channel counts, which count events.

```sh
uv run --extra analysis dwelly-bot analyze run dwelly_bot.analysis.banking --data dataset
uv run --extra analysis dwelly-bot analyze report --input analysis/artifacts/RUN/analysis.json --output analysis/artifacts/RUN/analysis.html
```

The `banking` recipe reads only `cases.json` and `documents/`, including reviewed text attachments available at the cutoff. Originals and later evidence are excluded. Use `--data .cache/datasets/banking-reviewed` for the corrected snapshot; `dataset/` is the historical v1 corpus.

For understanding how an example was handled and comparing a captured decision with later evidence, explicitly use the retrospective recipe:

```sh
uv run --extra analysis dwelly-bot analyze run dwelly_bot.analysis.banking_review \
  --data dataset --run experiments/baseline/results.json.gz
# Omit --run to inspect a different snapshot without mixing in another corpus's results.
uv run --extra analysis dwelly-bot analyze run dwelly_bot.analysis.banking_review \
  --data .cache/datasets/banking-reviewed
```

This recipe reads the **public** original index, complete history and text attachments. Its report is marked as retrospective, includes all cases, identifies the chosen cutoff and displays saved answers when supplied. It never runs an agent or judge, never imports private evaluator labels, and never treats the recorded outcome as a unique correct answer. Binary attachment hashes/paths are included for separate inspection; PDF text is not silently fabricated. Saved answers must come from the exact same pinned corpus. Review correct alternatives, unsupported claims, authority boundaries and necessary escalation; turn findings into agent changes only through the experiment workflow. Do not place this report or extracted later evidence in runtime retrieval.

Both recipes are offline by default. Shared helpers support profiling, sample review, text groups, semantic maps, quoted evidence extraction and optional model discovery. Use `configs/analysis.toml` only for explicitly requested paid work; it shares the cumulative Anthropic ledger. Source observations, model interpretations and verified operational effects remain distinct.

Without an API key, `--model-config configs/analysis-claude-code.toml --embedding-model lexical` runs model steps through the logged-in `claude` CLI (Claude Code subscription). Its separate ledger records API-equivalent list prices as a usage guard, not a bill.

Recipes expose `build(ctx) -> Report`. Keep dataset semantics in the recipe and reusable methods under `src/dwelly_bot/analysis/`. Reports contain source hashes, sample counts and limitations; generated HTML/JSON stay ignored under `analysis/artifacts/`. Pages builds only offline source analysis and saved execution reports. Analysis findings may change the agent only through the experiment workflow.
