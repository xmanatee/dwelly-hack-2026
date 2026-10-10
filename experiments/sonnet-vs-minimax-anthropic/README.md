# Sonnet 5.5 against MiniMax M3: complete Anthropic run

Hypothesis and fixed five-criterion rubric follow [the original protocol](../sonnet-vs-minimax/README.md). All 50 corrected banking cases, cutoff, actor prompt/tools and limits remain unchanged. MiniMax M3 is the saved OpenRouter control. Sonnet 5.5 runs through the direct Anthropic API; both actors receive a fresh full retrospective Opus 5.5 evaluation through that same direct API.

The original OpenRouter candidate completed 30/50 cases before HTTP 402 payment errors blocked 20 cases. Its results, spec, config and comparison remain under `../sonnet-vs-minimax/`; the partial OpenRouter evaluation reviewed 30/50 baseline answers and remains in `../minimax-baseline/openrouter-evaluation-incomplete.json.gz`. No completed captures or failed requests are discarded. This experiment reruns all 50 Sonnet cases with one consistent provider/config instead of mixing transports in a single run. The initial review is excluded from the final judgment totals, but its costs and failures remain reported.

This is a model-and-provider comparison: MiniMax uses OpenRouter, Sonnet uses Anthropic with prompt caching. Provider transport/caching can affect cost and latency, so differences are not attributed solely to model weights. The common direct Opus 5.5 judge does not receive actor identity. Model-family bias, subjective judgments and one sample per case remain limitations; no operational success or statistical significance is claimed. The requested MiniMax baseline stays active; Sonnet is not automatically adopted.

User-authorized paid scope includes finishing both full runs and reviews after provider failures. Existing Anthropic ledger spend is preserved while its local cumulative cap is raised from $20 to $100. OpenRouter failures keep their unresolved reservations. Direct Anthropic costs are configured-rate estimates, not invoices.

## Reproduce

```sh
uv run --extra evaluation dwelly-bot experiment run sonnet-vs-minimax-anthropic --baseline experiments/minimax-baseline/reference.json --config experiments/sonnet-vs-minimax-anthropic/config.json --description 'Sonnet 5.5 through Anthropic versus saved MiniMax M3 on all 50 reviewed banking cases'
uv run --extra evaluation dwelly-bot experiment evaluate --input ACTOR_RESULTS --output NEW_EVALUATED_RESULTS.json.gz --dataset dwelly-banking --dataset-root .cache/datasets/banking-reviewed --judge-config experiments/sonnet-vs-minimax-anthropic/judge-config.json --rubric experiments/sonnet-vs-minimax-anthropic/rubric.json --public-reference --concurrency 6
```
