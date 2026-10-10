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
public transfer/batch status, abuse, indirect crisis, a routine negative control, and synthetic scam/abuse messages. It is integration and
routing verification, not a paired quality experiment.

The saved baseline freshness check fails against current source. Preserve its existing
reference and captures; no baseline adoption or quality improvement is claimed. The extra
selection call has a latency/cost tradeoff. Full paired quality evaluation remains pending
an appropriate current control and review under the experiment workflow.

The first standalone smoke command stopped before any model call because the preparation script used `.json` while directory discovery expects `.input.json`. The script and filenames were corrected; no generated plan was overwritten.

## Saved live verification

- Runtime source: `69bcf21`; input-filename preparation fix: `6967e40`.
- **9 cases**, 24 settled requests, estimated **$0.3614503**; zero final failures.
- Four outputs required repair: three schema/enum issues and one missing required safety action. Original responses and repairs are retained.
- **315 offline tests**, Ruff and strict mypy passed.
- [Routing and plans](report.html), [Winner answers and reasoning](winner-report.html), [receipt](verification.json), and `captures.json.gz` preserve the actual results. No generated plan or answer was manually edited.
- The indirect crisis routed correctly; the age control had no safety flag; public status cases used supplied records directly. Winner 002 still includes a conditional follow-up lookup. Generic targets and wording about pending execution still need review; this is not a production-readiness or accuracy claim.

Reproduce into fresh destinations (model calls):

```sh
uv run python experiments/planner-modular-skills/prepare_smoke.py
uv run dwelly-bot plan --input experiments/planner-modular-skills/artifacts/inputs \
  --config experiments/planner-modular-skills/config.json \
  --output experiments/planner-modular-skills/artifacts/plans
uv run hackathon-winner --config experiments/planner-modular-skills/config.json \
  --output experiments/planner-modular-skills/artifacts/winner
```

`save_report.py` renders local captures and creates a non-overwriting archive, without model calls. Its source-commit and review notes describe this fixed smoke run; update those deliberately for a new experiment rather than relabelling old outputs.
