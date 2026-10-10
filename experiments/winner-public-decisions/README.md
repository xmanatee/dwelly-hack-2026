# Winner evaluation on public banking decisions

Evaluate the current Sonnet Planner and model answer generator on **all 50 Dwelly
public banking scenarios**, then independently review their saved outputs with
Opus. This is a new development control, not a comparison with the stale earlier
agent baseline or a hidden-challenge score. Runtime prompts and skills are frozen.

## Preparation

`preparation.json` explicitly selects **102 decision points** across all 50
histories. It includes initial operations, confirmation gates and later customer
replies. It excludes automatic final system updates and retrospective observation
notes where they are not discretionary actions. Exceptions are recorded in the
specification; multiple decisions from one scenario are correlated.

Each decision has two text files in separate trees:

```text
artifacts/prepared/
  inputs/001-e003/context.md       # Winner may read only inputs/
  references/001-e003/action.md    # Only the evaluator reads references/
  manifest.json                   # Source hashes, cutoffs, inclusion inventory
```

The context contains only preceding events and available attachment text, with a
neutral title. `index.md`, expected next event, later events and unavailable
attachments are excluded. Attachment timing comes from the reviewed
`configs/banking-development.json` profile. Original bytes remain unchanged.
The expected action quotes the next historical action verbatim, preserving its
scope and qualifications. Past-tense operations describe intended future actions
for this test; they never establish execution by Winner.

Some historical actions introduce checks or facts absent at the cutoff. The judge
marks this reference limitation and accepts safe alternatives. It does not demand
unseen balances, successful execution, exact wording or exact action enum labels.

## Reproduce

```sh
uv run --extra evaluation python -m dwelly_bot.adapters.banking_scenarios \
  --track '.cache/datasets/banking-reviewed/original/Banking & Financial Services' \
  --output experiments/winner-public-decisions/artifacts/prepared \
  --specification experiments/winner-public-decisions/preparation.json \
  --availability configs/banking-development.json

# Paid: current Planner -> model answer/reasoning generator; no bank effects.
uv run --extra evaluation hackathon-winner \
  experiments/winner-public-decisions/artifacts/prepared/inputs \
  --config experiments/winner-public-decisions/config.json \
  --output experiments/winner-public-decisions/artifacts/winner

# Paid: saved outputs only, using the shared bounded judge and provider pool.
uv run python -m dwelly_bot.evaluation.winner \
  --prepared experiments/winner-public-decisions/artifacts/prepared \
  --predictions experiments/winner-public-decisions/artifacts/winner \
  --judge-config experiments/winner-public-decisions/judge-config.json \
  --output experiments/winner-public-decisions/artifacts/graded
```

Use new preparation/prediction directories for another execution. Judging can resume
in the same grading directory only with identical inputs, evaluator and config;
completed or failed receipts are reused, never silently retried. Missing cases,
changed context/reference hashes and contradictory saved output files are errors.

## Assessment

Six separate criteria: Planner action, answer action, generator fidelity, factual
grounding, safety/scope, and reference assessability. Each has pass/fail/unknown
with cited evidence. Execution and judge errors remain in the assigned denominator.
All-core-pass means the first five criteria pass; reference assessability is
reported separately. Results are model judgments requiring case review. This
population was previously used to develop skills, so it is not a holdout.

Initial hypothesis: structured instructions and grounded rationales produce
specific decisions, but missing operational evidence may cause unnecessary gates,
referrals or invented details. The run will identify which errors belong to
Planner, generator or the reference split. No runtime tuning or baseline adoption
is part of this run. Findings and actual receipts will be added after evaluation.
