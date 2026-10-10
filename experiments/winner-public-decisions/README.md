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
is part of this run. Findings and actual receipts are recorded below.

## Results · 10 October 2026

[Portable report](report.html) includes every context, expected action, saved plan,
answer, reasoning and judge explanation, plus a separate manual review. The raw
judgments remain unchanged in `results.json.gz`; `review.json` records disagreements
without quietly changing scores. `captures.json.gz` preserves the exact prepared
text files, Winner outputs and journals. `verification.json` pins both source
receipts and archive hashes.

| Measure | Result, out of all 102 decisions |
| --- | ---: |
| Planner produced a valid plan | 99 |
| Planner + model generator completed | 98 |
| Opus reviews completed | 102 |
| Plan action: pass / fail / unknown | 82 / 13 / 7 |
| Answer action: pass / fail / unknown | 81 / 17 / 4 |
| Generator fidelity: pass / fail / unknown | 98 / 1 / 3 |
| Grounding: pass / fail / unknown | 93 / 7 / 2 |
| Safety/scope: pass / fail / unknown | 99 / 1 / 2 |
| Reference assessable: pass / unknown | 89 / 13 |
| All five core criteria passed | **77 (75.5%)** |

27 of 50 source scenarios passed all core criteria at every selected decision
point. These are **raw model judgments**, not verified accuracy. The three
missing plans remain in the denominator; there are no excluded cases or hidden
retries replacing failed outputs. A single scenario contributes one to three
correlated decisions, so decision and scenario rates answer different questions.

**Execution failures:** `009-e005`, `035-e005`, `043-e005` failed structured Planner
output after the allowed repair; `012-e004` retained a valid plan but failed the
answer guard. The first group combines malformed structured fields with invalid
evidence IDs during repair. The latter rejected a clearly labelled future draft
containing “I have sent”, despite its explicit non-execution disclaimer.

**Accounting:** 401 Winner requests, **$7.034523** ($4.9109864 Planner including skill
selection; $2.1235366 generator). Independent judging: **$4.125232**. Total:
**$11.159755** at configured accounting prices, not an invoice. Winner calls all
settled. `diagnostics.json` records 87 evidence-ID repair prompts, five schema
repairs and six completion-wording repairs.

## What this establishes — and what to change next

The complete context → shared Planner → model renderer → reference judge path now
runs on the entire public population. Later-stage replies generally use recorded
statuses well, and all 98 successful generator outputs passed the judge's fidelity
check. This supports testing a simpler renderer; it does not establish that a
template is equally good without an actual comparison.

The most actionable findings are:

1. **Fix citation mapping at the text boundary.** Each input is deliberately one
   complete Markdown document. Winner registers `context.md`, but the model often
   cites event numbers inside that document as independent evidence IDs. This
   preparation exposes a real single-document interface weakness and accounts for
   87 repairs. It must not be misreported as 87 bad banking decisions. Keep the
   text API and build canonical internal references, then compare on frozen cases.
2. **Choose the operation, not just a cautious message.** In `007-e003`, `024-e003`
   and `030-e003`, the plan should commit to a trace/journal/team check. Saying that
   no tools are connected or merely offering a review does not resolve the task.
   In `036-e005`, the customer already supplied and confirmed the address in the
   secure process; asking for it again loses the workflow state.
3. **Separate drafts from claimed effects.** A global phrase regex can reject a
   valid future reply. Represent message drafts and execution receipts separately
   instead of removing all completion guards or spending another retry on wording.
4. **Make evidence gaps explicit.** Message timestamps are not payment dates;
   secure chat is not proof of completed identification. Context collection should
   carry verified authority, operation identifiers and secure workflow references.
5. **Calibrate the reference judge before optimizing to its score.** Manual review
   found both a missed invented transfer date (`005-e003`) and false criticisms:
   misreading the speaker (`013-e004`), assuming a promised administrator check was
   completed (`045-e004`), and inconsistently grading an execution error as unsafe
   banking behaviour (`035-e005`). Some identifier questions are defensible when
   the reference introduces an identifier only after the cutoff (`003-e003`).

The manual audit is targeted, not a statistical judge-accuracy estimate. No raw
score is corrected, no failed output is replaced, and no Planner policy or baseline
is auto-adopted. This run establishes a reproducible control for future changes.
The initial corpus does not cover the breadth of fraud, vulnerability and crisis
cases in the synthetic corpus; this score cannot establish performance on them.

To inspect files from the tracked archive without the ignored working directory:

```python
import gzip, json
from pathlib import Path

files = json.loads(gzip.decompress(Path(
    'experiments/winner-public-decisions/captures.json.gz'
).read_bytes()))['files']
print(files['prepared/inputs/001-e003/context.md'])
print(files['prepared/references/001-e003/action.md'])
```
