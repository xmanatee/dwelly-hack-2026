# Planner decisions with public grounds

The previous Planner returned steps with `purpose`, mixing the action and its reason.
It also emitted speculative future branches and supplied the banking solver with advice
that explicitly permitted a new strategy. The user requires a final next-action decision.

Changes:

- Each step now has `instruction` and a separate `rationale`: explanation, evidence IDs,
  decision criterion and source. The overall `summary` states the chosen decision.
- Live validation requires grounds for every step, checks evidence and loaded rule sources,
  and rejects speculative `condition`/`escalate_if` branches. It does not prove that the
  natural-language rule is correctly interpreted; semantic review remains necessary.
- Missing essential input/authority means a specific request, verification procedure or
  handoff now; no presumed successful future check grants a state-changing operation.
- The downstream solver preserves the decision or stops on a blocker. Winner preserves
  grounds in both model/template rendering and its HTML inspection view.
- Existing saved `purpose` fields still parse as instructions. Historical missing grounds
  stay absent; original captures are not rewritten or given fabricated explanations.

This is a next-action decision, not a claim that the operation is already executed, and
not an integration of the advisory schema with the local product executor's separate
contract. The `proposed_action` and config `mode: advisory` names are retained for compatibility.

Validation uses the **same seven decision snapshots and two Winner cases** as
[the skill-routing smoke](../planner-modular-skills/README.md), to inspect actual output
semantics and formatting. The safety/synthetic cases include human support, scam,
unsafe contact, indirect crisis and an age negative control. No evaluation labels are
added to runtime input. Archive and compare shapes, not an invented quality score.

Hypothesis: explicit per-action grounds plus a current-decision boundary will produce
concrete next operations with inspectable justification, while preserving evidence and
execution limits. The tradeoff is a narrower plan horizon: later material evidence can
require another Planner call. No benchmark improvement is claimed or baseline adopted;
the saved benchmark reference is stale against current source and remains untouched.

```sh
# Use the immutable inputs produced by the previous smoke (or restore its capture archive).
uv run dwelly-bot plan --input experiments/planner-modular-skills/artifacts/inputs \
  --config experiments/planner-decision-contract/config.json \
  --output experiments/planner-decision-contract/artifacts/plans
uv run hackathon-winner --config experiments/planner-decision-contract/config.json \
  --output experiments/planner-decision-contract/artifacts/winner
```

Choose fresh output directories on a new run. Source/config are committed before model calls.
