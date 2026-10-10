# Project story

[← Project](../README.md) · [Product demo](../demo/README.md) · [Live voice runbook](../demo/LIVE-DEMO.md)

## The problem

A customer says a payment was sent; a record shows a debit; the recipient reports no money.
A useful service agent must separate established facts, conflicting evidence and missing
information before choosing a concrete next action.

## Our approach

```mermaid
flowchart LR
    T[Email / call / ticket] --> C[Scoped context]
    C --> P[Shared model Planner]
    K[Selected banking skills] --> P
    P --> E[Mock operational execution]
    D[Released challenge evidence] --> P
    P --> W[Winner answer + reasoning]
```

Context collection and decision-making are separate components. The Planner selects relevant
skills, applies them to supplied facts and produces a structured decision with explicit actions
and evidence-linked grounds. Product model mode and Hackathon Winner import this same component.
A missing material fact can lead to a concrete question or human handoff.

## Delivered

| Evidence | Delivered capability | Demonstration mode |
| --- | --- | --- |
| [30 final challenge outputs](../ANSWERS/README.md) | Opus 5.5 high completed the Planner → answer/reasoning path for every banking case. | 30 completed cases with evidence-linked proposed actions. |
| [Synthetic banking world](../local_testing/banking/README.md) | Separate state, incoming cases and evaluator material; scoped context and local pipeline. | Reproducible synthetic banking snapshots. |
| [Recorded product demo](../demo/dashboard.mp4) | Case desk and review workflow over earlier development results. | Historical development runs with review metrics. |
| [Voice demo](../demo/voice-call.mp4) | ElevenLabs conversation connected to the local tool/pipeline. | Live speech, prepared fixture plan and simulated handoff. |

## Next steps

Measure decision quality on held-out cases, connect authorized real action adapters, and
connect canonical model plans to the live speech path. Explicit action receipts and preserved inputs make each run traceable. The frozen
implementation and final outputs provide a reproducible foundation for these next steps.
