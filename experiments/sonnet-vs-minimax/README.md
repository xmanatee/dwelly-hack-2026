# Sonnet 5.5 against MiniMax M3

Hypothesis: changing only the actor model to Sonnet 5.5 improves grounded, actionable responses without implying unperformed bank operations. No prompt, skill, retrieval or tool changes are part of this experiment.

Both actors use OpenRouter, low reasoning effort, identical limits and the same 50 cases from `banking-reviewed-intake-v2` at `.cache/datasets/banking-reviewed`. Corpus SHA256: `29b6c89cdf3a78d8baa99d595452cd1b389dc106e07b4d263a5e1a59e9afd10e`. Case 041 includes its already uploaded CSV; eight later attachments are withheld. The historical v1 Sonnet result remains intact and is not this control.

All saved answers receive the same five-criterion Opus 5.5 review, with actor identity omitted from judge inputs. The evaluator reads verified original index/history and every original attachment (including extracted PDF text), labels them retrospective evidence, and respects the decision cutoff. Later events are examples, not a unique answer key. The judge has no operational tools. Native checks remain distinct from model judgments and actual operational success remains unknown. One judge, one sample per actor/case, and a judge from the Sonnet model family limit the strength of any winner claim.

The user explicitly authorized all 100 actor cases and their paid evaluation, relaxing prior local spending limits. Existing cumulative account spend and uncertain reservations remain in the shared ledger; its ceiling is raised to $100 for this task. OpenRouter provider-reported charges are retained per request; configured prices are conservative routing/reservation ceilings, not invoices. No telemetry or session capture is enabled.

Results and paired findings will be recorded after execution. MiniMax remains the requested baseline; the candidate is not automatically adopted.

## Reproduce

```sh
uv sync --locked --extra evaluation
uv run dwelly-bot run dwelly-banking --dataset-root .cache/datasets/banking-reviewed --config experiments/minimax-baseline/config.json --experiment minimax-baseline --artifacts experiments/minimax-baseline/artifacts
# Initialize the saved control from the generated results path:
uv run dwelly-bot experiment baseline init PATH_TO_BASELINE_RESULTS --config experiments/minimax-baseline/config.json --dataset-root .cache/datasets/banking-reviewed --output experiments/minimax-baseline/reference.json
uv run dwelly-bot experiment run sonnet-vs-minimax --baseline experiments/minimax-baseline/reference.json --config experiments/sonnet-vs-minimax/config.json --description 'Change actor from MiniMax M3 to Sonnet 5.5 on all 50 reviewed banking cases'
# Repeat for each saved actor result, using new output paths:
uv run --extra evaluation dwelly-bot experiment evaluate --input ACTOR_RESULTS --output NEW_EVALUATED_RESULTS.json.gz --dataset dwelly-banking --dataset-root .cache/datasets/banking-reviewed --judge-config experiments/sonnet-vs-minimax/judge-config.json --rubric experiments/sonnet-vs-minimax/rubric.json --public-reference --concurrency 6
```

The corpus root is pinned in each new reference; moving a run cannot silently revert it to the historical default dataset. Evaluations hash the exact public-reference payload as well as rubric, prompts, model settings and native checks. Input documents, outputs and cost receipts are retained in compressed evidence. The working tree's pre-existing change to `experiments/baseline/report.html` is unrelated to execution and is intentionally excluded from these commits; run receipts will honestly record a dirty tree.
