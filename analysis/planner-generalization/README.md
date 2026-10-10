# Planner generalization audit

Reviewed `592613e`, 2026-10-10. This is a source audit and experiment design, not evidence that an unseen-case benchmark passed. No runtime prompt, skill, model or accepted baseline was changed. No new model calls were made.

**No active skill is a memorized answer to a single scenario.** All eleven express reusable boundaries or procedures; no inspected instruction embeds public case IDs, fictional customer names, transaction amounts or exact expected answers. However, absence of literal leakage does not prove generalization. The library was developed from public histories and local synthetic/safety examples, and its topic coverage reflects those examples. Repeatedly optimizing against those same examples can overfit the evaluation even when every sentence sounds general.

The main risk is **coverage and composition**, not a secret per-case answer list: new evidence can invalidate an old procedure, multiple domains can impose conflicting constraints, and the fixed catalog cannot describe a missing topic. More model effort does not supply a missing fact, policy, permission or capability.

## Scope and reproduction

Inspected the active `src/dwelly_bot/planner/` prompt, evidence/safety rules, selector, all eleven skill bodies, catalog, source registry, banking action vocabulary, validator and orchestration; also Winner's adapter and the shared role/model wiring. `src/dwelly_bot/planning/implementation/` is a separate production placeholder, not the evaluated Winner implementation. Audit the active execution path, not that TODO.

```sh
uv run python analysis/planner-generalization/audit.py
```

Writes an offline self-contained HTML and JSON inventory under ignored `analysis/artifacts/planner-generalization/`. Captures source hashes, exact text, catalog/frontmatter consistency and the manual eleven-skill review. The literal scan is a navigation aid, not a proof of no semantic overfitting. Follow-up behavioral tests belong to the experiment workflow.

## Eleven-skill review

| Skill | Generalizable principle | Narrowness or missing boundary | Recommendation |
| --- | --- | --- | --- |
| payments | Distinguish payment identity and lifecycle states; don't invent settlement | Banking histories emphasize status replies; no general prioritization when another event changes the payment's purpose or risk | Keep; use a shared material-change rule rather than adding incident-specific payment variants |
| scheduled-payments | Instruction cancellation differs from refund, debt and contract | Recurring card payments are named but deeper guidance focuses on Direct Debit | Keep scheme distinctions; retrieve applicable scheme/procedure before treating all recurring payments alike |
| cards-access | Authentication scope, recovery, request versus completed state | Card, digital access, profile and closure are broad topics in one skill; many prohibitions can suppress a needed record check | Keep until retrieval evidence justifies splitting; state bank-owned inquiry and mutation separately |
| business-authority | Role is not operation authority; batch status is not line status | Examples center on payroll, signatories and file processing; “only named systems” can discourage a legitimate team request | Generalize to principal, resource, operation and approval scope; allow a responsible role when an API name is unavailable |
| fraud-takeover | Protect a risky operation; avoid credential collection and reimbursement promises | Listed scam stories can look like an exhaustive trigger list; historical events can get inappropriate urgency | State that examples are non-exhaustive; separate current exposure, historical dispute and evidence uncertainty |
| financial-abuse | Safe contact, confidentiality and limits of delegated authority | “next explicit condition” conflicts with the current no-conditions output contract; text mentions test scenarios | Make safe-contact determination a concrete next action; remove test-oriented phrasing in a future candidate without deleting the protection |
| vulnerability-support | Needs-based adjustments, hardship and proportionality | Hardship receives a generic referral; secured lending, collateral loss and interacting protections lack depth | Keep cross-cutting support; add a separately sourced debt/secured-lending module |
| bereavement-authority | Death notification differs from estate authority; joint/sole accounts differ | Legitimate domain-specific skill, not a single case; some rules are England/Wales-specific | Keep applicability explicit; do not apply death-specific rules to incapacity or a living attorney mandate |
| crisis-support | Immediate safety can take priority without banking authentication | Examples and source focus on mental health although description includes any immediate danger | Separate emergency triage from mental-health specifics; fire/injury must not automatically route to mental-health services |
| complaints-rights | Operational request and complaint are distinct; registration isn't remedy | Concrete complaint action can become unconditional once selected; repeated procedure risk | Require an actual new/unresolved complaint and check already registered/completed state |
| privacy-documents | Purpose, scope, recipient and disclosure authority | Injection protection is useful across every topic, not only documents; retention/conflicts need actual policy | Keep always-on injection handling and scoped disclosure; request applicable retention/legal policy rather than inventing it |

Domain specificity is useful: Direct Debit, powers of attorney and death notifications have different rules. Generalization means applying a rule across varied situations within its scope, not replacing every domain rule with vague universal advice.

## Common instructions and routing

Good existing boundaries: no future facts; assertions versus bank observations; proportionate support; no automatic vulnerability transfer; dependencies do not prove execution; no invented legal entitlement. The recent consent/date wording in `295f034` is expressed as general invariants, not case patches. Keep it and test it with different domains and wording.

Weaknesses:

- “Complete available snapshot” can be read as “all facts exist.” Distinguish *not supplied*, *not yet knowable*, *contradicted*, and *previously true but invalidated*.
- Winner TASK still requests “conditions/escalation criteria” while current Planner requires a concrete next decision and no speculative branches.
- “Decide now” should mean **decide the justified next action**, including a scoped specialist/research request. It cannot require deciding a final legal or insurance outcome with missing evidence.
- `financial-abuse` still uses “next explicit condition.” This is contract drift, not proof of memorization.
- The selector reads all catalog descriptions once, chooses at most six bodies, and shares the Planner model. It has no structured `uncovered_issue`, second selection pass, conflict report or difficulty route. `skill_selection: all` already loads all eleven for ablation, but is not a search over relevant combinations.
- The planner's advisory text already says to stop an affected action on new conflicting evidence and report it for a fresh decision. That is useful partial support. The inspected `make_plan` path does not implement automatic event-triggered replanning, model escalation, external research or semantic critique. Output repair checks format/evidence/flags, not whether the best strategy was chosen.
- `request_team_action` groups read/review with mutation; emergency handoff vocabulary is fraud/security/crisis-centric. Expanding skill prose alone will not solve an inadequate action catalog or an executor unable to invalidate stale plans.

## Missing capabilities: prioritize reusable mechanisms

| Priority | Capability | Why it generalizes | Existing partial coverage |
| --- | --- | --- | --- |
| P0 | Material event changes the case | Death, disaster, revocation, reversal, a court update or restored access can invalidate assumptions | Evidence conflict prose and advisory stop rule |
| P0 | Procedure state and safe interruption | Identify queued versus executed steps, pending deadlines, dependencies and stale decisions | `requires` and execution receipts, but no complete replan protocol in active Planner |
| P0 | Cross-domain conflict resolution | Keep immediate safety, legal constraints, authority and customer intent distinct; identify incompatible actions | Individual skills; no explicit composition review |
| P1 | Debt, arrears and secured lending | Affordability, forbearance, security/collateral, collection and enforcement status | Broad vulnerability support only |
| P1 | Insurance and asset damage | Policy terms, claim notification, assessment, repair and payment are distinct; coverage isn't automatic | No dedicated module |
| P1 | External legal constraints and jurisdiction | Orders, insolvency, sanctions/restrictions and representative authority need specific sources and temporal scope | General “do not invent law” plus bereavement/debt examples |
| P1 | Operational disruption and uncertain execution | Outages, duplicate events, partial execution and timeouts require reconciliation, not blind retry | Some payment-state rules |
| P2 | Dispute type and deadline ownership | Merchant dispute, unauthorized payment, scam and insurance claim follow different procedures | Payment/fraud/complaint modules, incomplete product coverage |
| P2 | Uncovered domain / missing policy | A finite catalog must admit it lacks a rule and request the precise missing knowledge | Generic handoff fallback |

P0 items belong mostly in shared reasoning/orchestration, not one new skill per disaster. Product modules should contain applicability, required facts, supported operations, stop conditions and official sources. Avoid adding a long checklist for every possible topic to every prompt.

## The mortgage / repossession / fire example

The robust behavior is to **reopen the decision**, not invent a universal fire exception. Establish which property/case the report concerns, event time, source certainty, immediate danger, prior action state and what the agent can actually control. A report is not yet an insurance coverage decision; extinguished historical damage differs from people in immediate danger.

If a visit or automated action depends on the property being safe/intact, stop *our affected pending dispatch where authorized*, or urgently request the responsible operator to suspend/review it. Do not claim to cancel a court order or completed external action. Preserve unaffected work and urgent deadlines. Pass the changed facts and unresolved issues to the appropriate lending/recovery, legal and insurance roles; gather the missing policy/claim/authority facts through supported channels. Use location-appropriate emergency routing only when immediate danger is actually indicated. Do not promise debt cancellation, insurance payment or an automatic end to proceedings.

These are proposed planning boundaries, not a legal conclusion about the hypothetical. FCA MCOB 13 contains mortgage-arrears/repossessions rules; insurance settlement depends on the claim, policy and circumstances. Those are separate domains requiring applicable evidence. [FCA MCOB 13](https://handbook.fca.org.uk/handbook/mcob13/), [Financial Ombudsman: settling home insurance claims](https://www.financial-ombudsman.org.uk/businesses/resolving-complaint/complaints-deal/insurance/home-buildings-insurance/settling-home-insurance-claims) (reviewed 2026-10-10; check jurisdiction and event-time rules).

## Next stage

Specify bounded stronger-model/research/review orchestration and contrastive tests before changing runtime. The objective is to detect unsupported final decisions and produce a useful, justified next operation—not to promise correctness by spending indefinitely. Routing and evaluator/optimizer patterns are established design options, but their benefit must be measured for this workload. [Anthropic: Building effective agents](https://www.anthropic.com/engineering/building-effective-agents).
