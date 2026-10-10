# Banking experiments

The first baseline assigns all 50 public banking development cases. Its tracked configuration uses Anthropic with the existing cumulative $20 account cap; the ledger also includes spend incurred before this dataset. Read costs as configured-rate estimates. Correctness has no trusted labels and remains unknown.

[Baseline report](baseline/report.html) · [Compressed execution evidence](baseline/results.json.gz) · [Reference](baseline/reference.json) · [Configuration](baseline/config.json).

## Change the agent

Commit execution code/configuration before paid runs. Follow the [experiment skill](../.agents/skills/dwelly-bot-experiment/SKILL.md). A comparison runs only the candidate and reuses the baseline's pinned cases, corpus and initial evidence.

```sh
uv run dwelly-bot experiment baseline check experiments/baseline/reference.json
uv run dwelly-bot experiment run NAME --config experiments/NAME/config.json --description "Concrete change"
uv run dwelly-bot experiment compare experiments/NAME/spec.json --output experiments/NAME/comparison.html
```

Keep every completed experiment's config, spec, compressed results and self-contained HTML, including failures. Accept only after review. The reference contains immutable content and execution fingerprints; report-only edits do not need a model rerun.

## Execution and recovery

```sh
uv run dwelly-bot run dwelly-banking --config experiments/baseline/config.json --experiment NAME
# Explicit subset for a development probe, not a full-baseline claim:
uv run dwelly-bot run dwelly-banking --ids banking-001,banking-035,banking-039 --experiment PROBE
uv run dwelly-bot monitor RUN_DIRECTORY
uv run dwelly-bot run dwelly-banking --resume RUN_DIRECTORY
```

`--resume` retains earlier attempts and costs and never reruns completed cases. Interrupted checkpoints stay in ignored `artifacts/`. Failed/unstarted cases remain in the denominator. Budget/time stops are execution failures, not business escalation. Local ledgers under `.cache/accounts/` are cumulative across agent, analysis and judge roles. Never delete them to obtain more allowance.

For the initial control only, initialize from the completed saved run:

```sh
uv run dwelly-bot experiment baseline init SAVED_RESULTS --config experiments/baseline/config.json --output experiments/baseline/reference.json
```

## Saved grading and export

```sh
uv run dwelly-bot experiment evaluate --input RESULTS.json.gz --dataset dwelly-banking --output REGRADED.json.gz
uv run dwelly-bot export --input RESULTS.json.gz --output EMPTY_DIRECTORY
```

Native checks inspect saved execution, answer presence, retrieval and cited-line existence. They do not infer operational correctness or safety. Optional paid judging is separate and requires explicit model configuration; it is not ground truth. Faithful export preserves actual outputs and failures. Public development results are not Reality Test submissions. No challenge adapter or unseen-case results are claimed yet.
