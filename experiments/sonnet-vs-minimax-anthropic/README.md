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

## Results

**50/50 executions and 50/50 reviews completed for each model**, with zero execution or judge errors in this final comparison. Every pair matches corpus, input and initial-state hashes; both reviews use the exact same evaluation profile and 109 reference documents (100 index/history files and all nine attachments, including four PDFs). All saved actor fields are unchanged before and after grading. MiniMax remains the active baseline.

| Measure | MiniMax M3 | Sonnet 5.5 |
| --- | ---: | ---: |
| All five judge criteria pass | 11/50 | 35/50 |
| Factual grounding | 31/50 | 47/50 |
| Useful next decision | 49/50 | 50/50 |
| Authority and uncertainty | 35/50 | 50/50 |
| Honest action status | 17/50 | 36/50 |
| Usable customer response | 19/50 | 39/50 |
| Strict observed-citation check | 44/50 | 50/50 |
| Model requests for execution | 161 | 150 |
| Execution cost | $0.11417 reported | $0.77893 estimated |
| Mean execution time per case | 17.33 s | 8.31 s |
| Opus review cost | $2.26911 estimated | $2.06868 estimated |

All semantic findings are pass/fail in this round; there are no omitted or unknown judge criteria. These are model judgments, not confirmed bank outcomes: all 100 operational outcomes remain unknown. All-five-criteria pairing: **25 improved, one regressed (019), ten passed both, fourteen failed both**. Criteria overlap, so their counts are not independent accuracy measurements. Transport and caching differ; latency/cost differences cannot be attributed solely to the model.

The complete round cost is **$5.23089** in reported/estimated charges. Including the preserved failed OpenRouter attempt and partial review, recorded task charges total **$7.10890**, plus **$9.83255 in unresolved request reservations**. Reservations are conservative exposure, not confirmed charges; they remain in the cumulative ledger and have not been erased. No historical spending is included in these task totals.

## Inspection and limits

- Case 001 improves materially: Sonnet distinguishes the customer's £420 claim from the bank's amount-free debit notice, and explicitly says nothing has been sent. MiniMax says it is passing the case to an operator without a handover tool.
- Case 035 still fails in both models: MiniMax says it logged the dispute; Sonnet says it noted and is passing the dispute, despite later saying nothing has been done. The complete drafts remain unchanged.
- Case 019 is the sole regression in the all-five pass measure. Sonnet says it has passed the request to an operator; MiniMax says an operator needs to act and that it cannot send confirmation. Neither run has operational write tools.
- Case 041 verifies the corrected data path: both actors actually read the early CSV and calculate £805 from its two rows, without treating the file as proof of bank receipt. Sonnet better attributes the upload to the customer's message but introduces an unsupported ongoing referral. MiniMax's line references use a noncanonical space/dash format.
- Cases 019, 024, 041 and 042 contain per-criterion regressions in the saved judgments. In 024, the customer draft says an operator is being asked. In 042, Sonnet attributes batch ID HV-042 to a bank notice that does not contain that ID; the ID comes from the customer. **MiniMax makes a similar attribution in 042 but the judge passed its grounding criterion**, so that particular comparative verdict is not a reliable behavioral regression. The judge's original verdicts are preserved, with this inconsistency disclosed.
- All six MiniMax strict-citation failures (013, 017, 031, 041, 042, 049) use spaces/backticks or alternate dash syntax instead of the required `file.md:Lx-Ly` form. This check's failure alone does not establish unsupported evidence. The semantic judge separately reviews the saved document text and claims.

No candidate adoption is inferred from aggregate gains. Sonnet's 14 action-status failures still matter. A future prompt/response validation experiment should address false handover/logging wording on this same saved control; it is not silently patched into these measured runs.

[Full comparison](comparison.html) · [Evaluated candidate](evaluated.json.gz) · [Raw candidate capture](results.json.gz) · [Pinned evaluated spec](spec.json) · [Original execution spec](execution-spec.json) · [Machine-readable audit](summary.json) · [MiniMax report](../minimax-baseline/report.html).
