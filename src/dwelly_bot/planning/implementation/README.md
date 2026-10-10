# Implementation moved to the shared Planner

Vera's implementation is in [dwelly_bot/planner](../../planner/README.md).
Its prompts, skill selection, evidence validation and canonical `Plan` are used by
both the product and [Hackathon Winner](../../../hackathon_winner/README.md).

`planner/service.py:DecisionPlanner` exposes `async plan(context: str) -> Plan` for
the product pipeline. Winner imports `make_plan` directly and owns answer generation.
This directory is retained as a pointer for earlier links, not a second implementation slot.

The parent `planning/` module remains the offline fixture contract. No migration of
historical saved plans or experiment captures is needed.
