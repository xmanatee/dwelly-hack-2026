# Project story

[← Project](../README.md) · [Demo storyboard](../demo/script.md)

## The idea

Operational service requests arrive through different channels, but the difficult work is shared: establish what is known, decide the right next step, and make the result observable.

Dwelly-bot makes those responsibilities explicit. A context investigator gathers useful evidence. A Planner applies knowledge to that evidence and chooses concrete actions. An executor carries them out and records what happened. A human handoff is a legitimate decision, not a failure to produce a long answer.

## Why this architecture fits the hackathon

The Planner is our central hypothesis: a reusable decision component can serve both a live operational workflow and a case-based evaluation. A contest adapter supplies prepared evidence; production builds it from sources. The same Planner is intended to sit behind both.

We aim to sharpen that component using Dwelly cases and synthetic operating scenarios: incomplete records, misleading signals, ambiguous identities and failed actions. The two loops help distinguish a poor decision from a context-gathering or execution failure.

## Say today / update before launch

| Accurate today | Replace with measured evidence later |
| --- | --- |
| The pipeline runs through email, call and ticket fixtures. | Real channel integration and operational outcomes. |
| Context reads synthetic bank snapshots and threads; three live model smokes are captured. | Broad retrieval quality and temporal entity-state coverage. |
| The Planner interface and action profiles are implemented. | Vera's final model, skill hierarchy and decision examples. |
| Local arithmetic and persistent mock receipts work. | Provider-confirmed effects and recovery behavior. |
| Historical banking experiments are saved. | A new evaluation of this Planner and Solver. |

The final launch story should replace these slots with actual implementation links, an observed case and a playable demo. Do not describe the current stub as an advanced multi-agent planner or transfer the earlier agent's scores to it.
