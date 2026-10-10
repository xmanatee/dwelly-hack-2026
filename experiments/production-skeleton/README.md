# First production vertical slice (offline implementation)

Hypothesis: separating intake, context, a `text -> Plan` component and execution makes
the production path independently replaceable while keeping the same Planner API for
the future Hackathon Solver. This is an implementation scaffold, not a quality candidate
or adoption of a new banking policy. The planner always requests human review.

The historical baseline freshness check passed before editing. Its reference and saved
captures remain unchanged. There is no meaningful quality comparison between that agent
and a constant placeholder; no paid experiment or baseline promotion is performed here.

## Source review behind the interfaces

Offline `banking_review` on `.cache/datasets/banking-reviewed` covered all 50 public
banking examples and 258 historical events. Event channels: 86 secure portal, 86 internal
note, 38 secure chat, 23 business portal, 16 verified call, 9 external message. These are
event counts, not customers. Email and assigned tickets are requested product channels;
the corpus does not explicitly classify events as email or tickets.

The complete index/history of 001, 032, 039 and 041 were inspected as representative
examples, not an exhaustive action taxonomy. They suggest source interfaces for transaction
journals, archive records, customer/session context and file receipts, plus actions for
human referral, communication and case updates. They do not supply a live bank API or
prove permissions to perform financial operations. The implementation adds communication
and handoff categories only; it does not mine policies or replay later history as data.

The review's HTML/JSON remain under ignored `analysis/artifacts/`. Original case bytes
remain unchanged. Demo inputs are newly authored fixtures, separate from the corpus.

## Layered delivery

1. Channel normalization, context-source/extraction interfaces and Markdown output.
2. Public Planner/Plan with a human-review stub and categorized mock execution.
3. Local orchestration, three-channel demo, traces and integration tests.

The fixed demo configuration uses no model, no paid budget and no network. Real model
implementations must reuse the existing model pool/budget/trace infrastructure; a real
Planner will need a new control round on this contract before quality claims.
