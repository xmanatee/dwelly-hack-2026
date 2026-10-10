# Modular Planner knowledge

Hypothesis: a small semantic selection step plus focused banking skills makes case handling
more maintainable and relevant than a single domain prompt. General evidence/authority and
critical triage rules remain always loaded. Selection and planning use the same configured
Planner model and shared runtime; the public `PlanInput -> Plan` interface is unchanged.

## Source study

Reviewed 50 original organizer banking histories, 28 local safety histories, and the
1,180-case decision-time synthetic message inventory. Transparent multi-label lexical
screening helps navigation; selected histories/messages were manually inspected. No private
labels, expected next actions, final entity database, or benchmark answers enter knowledge.
Full public/test histories are retrospective analysis only, never new runtime case evidence.

- Public 001/005/016: distinguish sending, recall/review registration and actual credit/refund.
- Public 021–030: separate card dispatch, restriction, recovery and profile change states.
- Public 041–050, especially 042/044: file receipt, validation, approval and per-line execution
  are separate; permission to see a report is not permission to release funds.
- Safety 107 and synthetic SYN-0421: an ordinary banking task can require safe-contact
  handling before any email, call or letter.
- Safety 109: indirect crisis disclosure is missed by the initial literal keyword screen.
  This is a concrete reason to route semantically, not by matching trigger words.
- Synthetic SYN-0077, SYN-0173, SYN-0497: scam recovery, estate authority and reported debt
  protection need different actions and evidence gates.
- Safety 126–128: age, amount and frustration are useful negative controls for over-escalation.

| Corpus | Cases | Cases with any lexical match |
| --- | ---: | ---: |
| Original histories | 50 | 50 |
| Local safety histories | 28 | 25 |
| Synthetic decision-time messages | 1,180 | 867 |

These are screening counts, not classified topic coverage or quality scores. The regex
patterns, matches, examples and input hashes are reproducible via the offline recipe:

```sh
uv run --extra analysis dwelly-bot analyze run dwelly_bot.analysis.planner_topics \
  --data '.cache/datasets/banking-reviewed/original/Banking & Financial Services' \
  --output analysis/artifacts/planner-topics-public
uv run --extra analysis dwelly-bot analyze run dwelly_bot.analysis.planner_topics \
  --data 'experiments/safety-cases/Banking & Financial Services' \
  --output analysis/artifacts/planner-topics-safety
uv run --extra analysis dwelly-bot analyze run dwelly_bot.analysis.planner_topics \
  --data local_testing/banking/data/seed-2026 \
  --output analysis/artifacts/planner-topics-synthetic
```

Use fresh destinations on repeat runs. Generated source reports remain local/ignored.

## Knowledge and validation

[Runtime skill library](../../src/dwelly_bot/planner/skills/README.md) contains eleven
skills and reviewed official sources. Existing action/safety vocabulary and Plan validation
remain unchanged. No giant external prompt, repository code or evaluator logic is imported.

Offline tests cover selection isolation, common rules with no topical match, invalid IDs,
duplicates, repair, resource packaging, visible failures, shared request limits and Winner
integration. A live smoke uses the two bundled Winner cases and decision-time inputs for
mixed abuse/payment, indirect crisis and a routine negative control. It is integration and
routing verification, not a paired quality experiment.

The saved baseline freshness check fails against current source. Preserve its existing
reference and captures; no baseline adoption or quality improvement is claimed. The extra
selection call has a latency/cost tradeoff. Full paired quality evaluation remains pending
an appropriate current control and review under the experiment workflow.
