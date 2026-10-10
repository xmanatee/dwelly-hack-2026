---
name: dwelly-bot-experiment
description: Change dwelly-bot agent behaviour, models, runtime prompts/skills, retrieval or tools using a saved baseline and a reviewed two-run comparison.
---

# Improve the agent

- Follow `dwelly-bot-repo-sync` before editing. Run `dwelly-bot experiment baseline check experiments/baseline/reference.json`; preserve that reference before changing the agent; after editing, do not require the baseline to match the candidate code. See [commands and schema](../../../experiments/README.md#change-the-agent).
- Missing baseline evidence blocks comparisons and adoption, not requested implementation or offline tests. Obtain the team’s saved run before an experiment; creating the first control requires an explicit task. Never substitute fixture/demo results or claim improvement without a comparison. A subset baseline only supports subset claims.
- Put the hypothesis, concrete changes and tracked config in `experiments/<name>/`; use ignored `artifacts/` only for working checkpoints. Commit source/config before the run so its Git receipt is reproducible. Reuse `src/dwelly_bot/`, never copy the agent. Keep prompt prose in package resources and tool boundaries and execution traces mandatory.
- Reuse the baseline's assigned cases, corpus and initial evidence. Resolve paid-run scope/budget only if not already authorized; materialize CLI overrides in the tracked config before the final run. Local budget ledgers do not enforce a team-wide cap across laptops.
- Run `dwelly-bot experiment run NAME --config PATH --description "CHANGE"`: it reads the saved baseline, executes/evaluates only the candidate, and saves the pinned spec and comparison HTML. `compare` rerenders saved results without model calls.
- Inspect improvements, regressions, unknowns, execution errors, critical flags and cost; run affected offline checks. Present the concrete report and tradeoffs to the user. Aggregate gains never auto-approve a change.
- After the user accepts, synchronize again. Reuse the run if its execution fingerprint/config still match; otherwise rerun the combined candidate. If the accepted reference changed, rebuild the comparison and obtain acceptance of that new comparison.
- Run `dwelly-bot experiment baseline accept SPEC --output experiments/baseline/reference.json`; commit accepted code/config/spec/reference together when authorized. Keep compressed results and self-contained comparison HTML in Git for every experiment, accepted or rejected; record the assessment in the spec’s `conclusion`. Keep referenced paths and bytes unchanged.
- Tests, docs, comments and report/analysis changes need no action rerun. Dependency changes are conservatively stale; the freshness check is not a proof of semantic equivalence. Evaluation-only changes reuse captures; native baseline regrading is automatic and paid judges stay explicit. New metrics appear automatically; missing or differently versioned values have no delta; changed corpus/case selection starts a new control round. Keep failures visible.
