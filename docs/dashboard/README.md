# Case desk dashboard

An operator-facing view of dwelly-bot on the 50 public banking cases: the queue of cases that need a
person, each case's drafted reply and proposed operator action, the independent quality review, and
handling time and model cost. A switch compares Sonnet 5.5 with the MiniMax M3 control.

[Open the dashboard](https://claude.ai/artifact/9YDXS6aN5dMsfreZVKM6EG) (shared from claude.ai; ask the owner for access if it does not open).

## Data

Everything comes from saved runs already in this repository; nothing is re-executed.

| File | Built from |
| --- | --- |
| `cases.csv` | `experiments/minimax-baseline/evaluated.json.gz`, `experiments/sonnet-vs-minimax-anthropic/evaluated.json.gz`, plus title, channel and customer from the reviewed public corpus |
| `answers.csv` | the same two runs: request, drafted reply, operator plan, rationale, documents read, reviewer notes |
| `criteria.csv`, `resources.csv` | `experiments/sonnet-vs-minimax-anthropic/summary.json` |

```sh
uv run python docs/dashboard/build_data.py --output .cache/dashboard
```

Requires the reviewed corpus at `.cache/datasets/banking-reviewed` ([dataset install](../../dataset/README.md)). No model calls.

## Reading it

- "Needs an operator" and "Waiting on customer" are the agent's proposed dispositions. The agent has read-only evidence tools; every reply is a draft and every action a proposal.
- "Quality review" is the Opus 5.5 retrospective judgment from the saved runs, not a confirmed bank outcome.
- Request type groups the public cases by their organiser numbering (001–010 payments, 011–020 scheduled payments, 021–030 cards and access, 031–040 statements, fees and profile, 041–050 business banking).
- Sonnet cost is a configured-rate estimate; MiniMax cost is provider-reported. Transport and caching differ between the two.
