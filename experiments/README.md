# Banking experiments

The active [MiniMax M3 baseline](minimax-baseline/README.md) and [Sonnet 5.5 experiment](sonnet-vs-minimax-anthropic/README.md) each execute all **50 banking development cases** on the corrected v2 snapshot. Each saved answer receives native checks and the same five-criterion Opus 5.5 retrospective review. Acting models see only the initial request, first two events and the already available case 041 CSV. The judge alone sees complete public case histories and all nine attachments.

[Full comparison](sonnet-vs-minimax-anthropic/comparison.html) · [MiniMax report](minimax-baseline/report.html) · [Active reference](baseline/reference.json) · [Evaluation protocol and results](sonnet-vs-minimax-anthropic/README.md).

MiniMax uses OpenRouter; Sonnet and the shared judge use direct Anthropic. An earlier [OpenRouter Sonnet attempt](sonnet-vs-minimax/README.md) and baseline review each stopped at 30 completed cases/reviews because the provider returned HTTP 402. Those partial results, costs and unresolved reservations are preserved. They are excluded from the completed comparison. Native citation checks measure observed line references; model judgments assess answer quality; independently verified bank outcomes remain unknown. Sonnet has not been adopted over the requested MiniMax control.

## Historical v1 control

The original Sonnet control used two events and no attachments. It executed 50/50 cases for $0.7832 estimated new spend and 150 model requests; all native presence/retrieval/citation checks passed, but all outcomes remained unknown. Its 35 escalated and 15 needs-info answers remain unchanged. Cases 001 and 035 contain unsupported draft handover/logging wording. Changing to the reviewed v2 evidence required the new control round above.

[Historical report](baseline/report.html) · [Original evidence](baseline/results.json.gz) · [Historical reference](baseline/historical-reference.json) · [Original configuration](baseline/config.json).

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
uv run dwelly-bot run dwelly-banking --dataset-root .cache/datasets/banking-reviewed --config experiments/minimax-baseline/config.json --experiment NAME
# Explicit subset for a development probe, not a full-baseline claim:
uv run dwelly-bot run dwelly-banking --dataset-root .cache/datasets/banking-reviewed --config experiments/minimax-baseline/config.json --ids banking-001,banking-035,banking-039 --experiment PROBE
uv run dwelly-bot monitor RUN_DIRECTORY
uv run dwelly-bot run dwelly-banking --resume RUN_DIRECTORY
```

`--resume` retains earlier attempts and costs and never reruns completed cases. Interrupted checkpoints stay in ignored `artifacts/`. Failed/unstarted cases remain in the denominator. Budget/time stops are execution failures, not business escalation. Local ledgers under `.cache/accounts/` are cumulative across agent, analysis and judge roles. Never delete them to obtain more allowance.

For an explicitly authorized new control round, initialize from the completed saved run into a new directory:

```sh
uv run dwelly-bot experiment baseline init SAVED_RESULTS --config experiments/NEW_CONTROL/config.json --dataset-root .cache/datasets/banking-reviewed --output experiments/NEW_CONTROL/reference.json
```

## Saved grading and export

```sh
uv run dwelly-bot experiment evaluate --input RESULTS.json.gz --dataset dwelly-banking --dataset-root .cache/datasets/banking-reviewed --output REGRADED.json.gz
uv run dwelly-bot export --input RESULTS.json.gz --output EMPTY_DIRECTORY
```

Native checks inspect saved execution, answer presence, retrieval and cited-line existence. They do not infer operational correctness or safety. Optional paid judging is separate and requires explicit model configuration; it is not ground truth. Faithful export preserves actual outputs and failures. Public development results are not Reality Test submissions. No challenge adapter or unseen-case results are claimed yet.

Use `dwelly_bot.analysis.banking_review` to inspect saved outputs beside complete public examples and later evidence; see [analysis usage](../analysis/README.md). The recorded actions are retrospective reference material, not callable tools. Public development export to `ANSWERS/` is rejected; use an ignored `experiments/NAME/artifacts/review-export/` folder, which is labelled as development-only.
