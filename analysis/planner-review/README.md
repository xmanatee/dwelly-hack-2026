# Planner decision review

The main weakness is choosing the next operation when a bank-owned fact is missing, not loading too many skills. The current Planner usually handles an already supplied bank result well. It sometimes treats “no tools connected” as a reason to stop at a holding reply or ask the customer to investigate bank records. It also loses workflow state and occasionally adds unnecessary procedures. More blanket safety prose would likely obscure the distinction further.

This is an **offline diagnosis and proposal**, not an adopted runtime change or a new benchmark. Saved judgments remain unchanged. The examples below refer to public development data; do not put them, expected next events or this report in runtime retrieval.

## Evidence and reproduction

Source: [winner-public-decisions](../../experiments/winner-public-decisions/README.md), its tracked `results.json.gz` and `captures.json.gz`. The run used Sonnet 5.5 for Planner/generation and Opus 5.5 for judging. Execution source was `a867cbc`; the reviewed checkout was `2057efc`. The inspected Planner, harness runtime, Winner adapter/runner and generator had no source diff between those commits. All seven actually loaded skill files matched their captured hashes.

```sh
uv run --extra analysis dwelly-bot analyze run analysis/planner-review/recipe.py \
  --data experiments/winner-public-decisions
```

The command prints the report path. A fresh output directory contains `analysis.html`, `analysis.json` and `findings.json`; no model configuration, API key or live grading is used. To choose a new destination, add `--output analysis/artifacts/planner-review-RUN`. Generated reports remain ignored. The recipe checks that grader inputs equal prepared contexts and Winner contexts differ only by their document heading and terminal newline normalization.

[review.json](review.json) holds explicit manual interpretations, confidence and case IDs. [recipe.py](recipe.py) derives counts from the saved population and produces a searchable drilldown containing context, withheld reference, plan, answer, public rationale, original judge and review notes for **all 102 decisions**.

Review coverage: all 102 compact records; all 31 records with at least one non-pass criterion; targeted suspicious passes; eight ordinary all-criteria-pass controls chosen using `random.Random(20261010)`: `031-e005`, `021-e005`, `004-e005`, `022-e005`, `029-e005`, `037-e005`, `028-e004`, `032-e006`. The ordinary controls correctly distinguish dispatch from receipt, request from completed change, and started process from confirmed result. The review is a reasoned reading of saved evidence, not an independent expert gold annotation.

| Measure | Saved result |
| --- | ---: |
| Source scenarios / decision cuts | 50 / 102 |
| Valid plans / complete generated outputs | 99 / 98 |
| Planner action: pass / fail / unknown | 82 / 13 / 7 |
| Answer action: pass / fail / unknown | 81 / 17 / 4 |
| Generator fidelity: pass / fail / unknown | 98 / 1 / 3 |
| Grounding: pass / fail / unknown | 93 / 7 / 2 |
| Safety/scope: pass / fail / unknown | 99 / 1 / 2 |
| Reference assessable: pass / unknown | 89 / 13 |
| All five core criteria pass | 77 / 102 |
| First selected cut per scenario: action pass | 35 / 50 |
| Later cuts: action pass | 47 / 52 |

First/later performance is observational, not a causal experiment. Multiple cuts from one history are correlated. These public cases have already informed skills; excellent performance here would not establish generalization.

## What is actually wrong

### 1. A missing bank fact becomes a customer question or a premature ending

Seven clear action failures: `007-e003`, `010-e003`, `018-e003`, `024-e003`, `029-e003`, `030-e003`, `050-e003`. The relevant topical skills were already selected in all seven.

| Example | Actual decision | Needed next decision |
| --- | --- | --- |
| `007-e003` international payment stage | Repeats uncertainty and points toward the beneficiary bank | Request the bank's payment-status/trace check; do not invent its outcome |
| `010-e003` matching incoming refund | Asks the customer for incoming transaction details | Check the incoming records against the known outgoing payment |
| `018-e003` two similar payment lines | Asks the customer to identify their types/references | Inspect the instruction journal to identify them; do not cancel either yet |
| `024-e003` card restriction | Offers that a card team could check | Commit a specific restriction/category check as a plan step |
| `029-e003` device link | Sends customer to self-check/restart, without a supplied procedure | Request the device/access log check |
| `030-e003` known request reference | Summary offers review; steps only reply | Put the review against the supplied request reference into steps |
| `050-e003` authorized supplier payment | Repeats authorization, leaves no missing fact, marks completed | Investigate the execution stage; authorization is not arrival |

The general prompt does say to obtain a decision-changing missing fact, and the payments skill explicitly says to request a named journal lookup for a material gap. The problem is inconsistent application, not an absent “payments” skill. “No tools” describes Planner's runtime capability, not the set of operations its plan may instruct an executor or bank team to perform.

### 2. The plan forgets what has already happened

In `036-e005`, a new address has been entered and confirmed through the secure workflow. Its literal text is not printed in the conversation. Planner asks for it again. The correct abstraction is “continue the existing confirmed request,” not “invent the address” or “collect it again.” In `016-e005`, review is already registered as HV016, yet an additional reason/bill becomes a new blocking prerequisite. Useful supporting material is not automatically mandatory.

Use a small workflow-state summary: requested operation, evidence of steps already completed, pending operation, supplied workflow handle and unresolved prerequisites. It can remain internal to plan generation; a large new public schema is unnecessary.

### 3. Restriction is sometimes excessive, but not because all skills are loaded

Actual selections: one skill in **77/102**, two in **23/102**, three in **2/102**. Frequencies: payments 39, cards-access 27, business-authority 21, scheduled-payments 20, privacy-documents 14, fraud-takeover 4, complaints-rights 4. Vulnerability, bereavement, crisis and financial-abuse skills were never selected. General safety instructions were still loaded. Most passive failures have no raised safety flag.

Do not delete those unexercised safety skills based on this dataset. The more useful ablation is whether clearer core instructions and applicability conditions improve decisions with the same selection.

Suspicious **judge-passed** plans reveal the opposite error:

- `039-e004` / `039-e006`: a July sign-in notification discussed in October produces urgent security escalation without supplied evidence of an active compromise. Ordinary security review may be justified; urgency needs a current risk signal.
- `034-e005`: the tariff check has returned a result, yet the earlier word “escalate” triggers another complaint procedure. Distinguish an unresolved complaint from a completed factual check and from an already registered procedure. The tariff result does not itself prove that every complaint is resolved.
- `006-e005`: a status question and “I intended one payment” become a stop review “at the customer's request.” This is a review request, not an executed cancellation, but inferred intent is being upgraded into explicit consent.
- `040-e003` and `047-e003`: the actual document or authority operation remains an offer, a prose fallback or a summary statement instead of a committed step. `condition=null` alone does not remove hypothetical branches.

### 4. Evidence provenance is inconsistent

`010-e005`, `012-e003`, `030-e003`, `038-e003` treat a secure channel as established identity. Conversely, `008-e003` demands a separate verification record despite a customer's report of completing checks. That report is not a trusted bank verification; the fix is a consistent provenance policy, not trusting every assertion. The context collector should expose verification status, source and scope when it has them.

In `005-e003`, the notification timestamp becomes the transfer date. Distinguish message time, operation time, customer claim and bank observation. Unknown facts must stay unknown, without preventing an internal request to resolve them.

### 5. Technical retries obscure decision quality

The journals contain **87 evidence-ID repair prompts across 87 cases**, five schema repairs and six generator wording repairs. Prepared contexts use `### ... event 001` headings; the history parser expects a different format and registers the whole text as `context.md`. The model sees event labels but only `request` and `context.md` are valid citation IDs. This is an adapter/evidence-contract weakness exposed by the preparation format, not 87 distinct reasoning failures.

`009-e005`, `035-e005`, `043-e005` fail to produce a valid plan: malformed list fields and subsequent invalid citations exhaust the single repair allowance. Increasing retries alone would mask the issue. Give the model an explicit canonical evidence registry and include allowed IDs in validation feedback. Preserve the long-text external API; the adapter can assign internal IDs without injecting later events. Consider a smaller generation schema and separate format repair from semantic replanning, after offline provider/schema checks.

`012-e004` preserves a plan but loses the final output: the generator guard matches “I have sent” inside an explicitly future draft. Keep the prohibition on false execution claims, but scope it to execution assertions rather than draft or historical quotations. All 98 successfully generated outputs pass fidelity, which does not prove their decisions were good. A deterministic rendering experiment on saved plans can test whether another generative stage earns its complexity; no quality gain is established yet.

## Where the evaluation itself misleads

The 13 raw Planner-action failures split into **eight clear operational/state gaps**, **four ambiguous prerequisite cases**, and **one likely judge false positive**. This is a manual interpretation, not a corrected score.

- `002-e003`, `003-e003`, `031-e003`, `048-e003`: the reference implicitly uses an identifier, account/session or authority context not explicit at the cutoff. Minimal clarification may be appropriate. There can still be excessive questioning or a missing bank-owned check, but these are not clean gold failures.
- `045-e004`: the reference introduces a verified administrator; visible history only promises a check. Do not reward sending access material to an administrator whose authority is not yet established.
- `013-e004`: the judge misreads the speaker of an identification claim. Planner correctly attributes it to the customer.
- `035-e005`: no valid plan exists. A grounding/safety failure here cannot establish a harmful decision; equivalent failures elsewhere are unknown.

The rubric already warns against these mistakes. Adding more rubric prose alone is unlikely to fix them. Annotate each disputed reference with **minimal required action, acceptable alternatives, prerequisites known at the cutoff, prerequisites unknown, and forbidden assumptions**. Require the judge to identify the supporting speaker/event for claimed facts. Preserve raw scores and publish adjudication separately. Keep technical success, decision quality and output fidelity separate.

## Proposed changes, in order

| Priority | Location | Proposed change | Evidence / acceptance check |
| --- | --- | --- | --- |
| P0 | [Winner adapter](../../src/hackathon_winner/adapters.py), [evidence prompt](../../src/dwelly_bot/planner/evidence.md), [validator](../../src/dwelly_bot/planner/validate.py) | Expose canonical citation IDs; repair with the allowed registry. Align Winner TASK's legacy “conditions/escalation criteria” wording with final next-action decisions. | No future facts introduced; valid plans for all assigned inputs; citation repairs fall from 87. Judge quality must not regress. |
| P1 | [Core prompt](../../src/dwelly_bot/planner/prompt.md), evidence instructions | One shared gap-ownership and workflow-state rule, replacing duplicated restrictions. “All currently available context” does not mean “every bank fact is known.” | Concrete next operations in the seven missing-check cases; reuse existing workflow in 036; no repeat lookup in ordinary controls. |
| P1 | [Action vocabulary](../../src/dwelly_bot/planner/playbooks/banking.json), validator | Separate internal read/review, disclosure and mutation. `request_team_action` currently mixes review with block/revoke/register and is entirely classed as state-changing. Use trusted operation classes, not a free-form model claim that identity is unnecessary. | Internal inquiry does not require the same gate as a funds/access change; unauthorized disclosure/mutation remains blocked. This is a structural concern, not a demonstrated cause of the observed repairs. |
| P1 | [Cards](../../src/dwelly_bot/planner/skills/cards-access/SKILL.md), [scheduled payments](../../src/dwelly_bot/planner/skills/scheduled-payments/SKILL.md), [documents](../../src/dwelly_bot/planner/skills/privacy-documents/SKILL.md), [business authority](../../src/dwelly_bot/planner/skills/business-authority/SKILL.md) | Missing record -> explicit responsible bank operation; already known record -> direct reply. Resume an existing procedure. Ask only essential customer-owned inputs; responsible team names are sufficient when no API is supplied. | No invented UI/queue, no repeated collection of an existing value, no optional document promoted to prerequisite. |
| P1 | [Fraud](../../src/dwelly_bot/planner/skills/fraud-takeover/SKILL.md), [complaints](../../src/dwelly_bot/planner/skills/complaints-rights/SKILL.md) | Add concise applicability and stop conditions: current danger vs historical audit, new/unresolved complaint vs completed or already registered procedure. Selected skill does not mean every action in it applies. | Avoid unsupported urgency/duplicates on 039/034 while preserving escalation on genuinely active-risk regression cases. |
| P2 | Planner generation / validation | Bounded semantic review: does the step resolve the stated goal; who owns the gap; what is already done; has consent expanded; do summary, steps and disposition agree; are assertions grounded? | Start with one integrated review checklist. Test one extra critic only if it demonstrably helps; current retries repair schema/evidence, not strategy. Do not create an unbounded multi-agent loop. |
| P2 | [Generator](../../src/hackathon_winner/generation/__init__.py) | Distinguish future message drafts, historical observations and verified execution receipts. | 012 completes without weakening the no-false-execution guarantee; renderer preserves the selected decision. |

Keep the public decision simple: a concrete next operation plus public grounds and dependencies. A request to inspect a record is itself a final next decision. Its unknown result does not justify appending a speculative future approval/refund. The executor can return new evidence for another invocation of the same Planner.

## Experiment sequence

1. **Technical contract only.** Commit adapter/citation/repair changes and run the same 102 contexts with the same model/config. Record completion and repairs separately from decision scores. Preserve every failed output.
2. **Core decision rule.** With the technical baseline fixed, change only gap ownership/workflow-state instructions. Compare actual steps on the seven clear missing-check cases, 036/016, all ordinary controls, and the entire corpus. Adjudicate disputed references rather than optimizing their raw fail labels.
3. **Applicability and operation classes.** Test narrowly scoped fraud/complaint gates and read/review versus disclosure/mutation. Add separate synthetic regression cases for active fraud, unknown authority and vulnerable-customer support; this public population cannot establish their safety.
4. **Iteration or rendering.** Compare integrated review against one bounded semantic critic only if residual decision errors justify it. Separately compare template rendering with the existing generator on identical saved plans. Measure quality, latency, requests and cost; do not mix all changes into one candidate.

Split any tuning/validation partition by original **scenario**, not by decision cut. Keep a separate unseen synthetic or organizer holdout. A high score on this repeatedly inspected public set is a development result. Runtime changes require the repository experiment workflow; this review changes neither prompts nor accepted baseline.
