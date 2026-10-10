# REASONING — Case 022 (Available balance after a card purchase)

Full input is saved in `context.md`. This memo sets out the public grounds for the plan of record; nothing below has been executed.

## 1. Situation and history

- **E01 (2026-11-10 09:00, internal card view):** Card ledger entries retrieved for account SYN-ACCT-B022 (`attachments/card-entries.csv`). Account holder Rois Fenwick; current contact authentication recorded as passed.
- **E02 (09:10, authenticated chat):** Customer reports "the hotel took £600 and £520, so that is £1,120"; available balance only £380; expected the stay to cost £520. This is the customer's interpretation, not a ledger fact.
- **E03 (09:15, merchant email, bank copied):** Alderclock Hotel sends the final stay receipt (`attachments/hotel-receipt.pdf`, SYN-HOTEL-022): stay 2026-11-07 to 2026-11-10, final amount paid by card £520.00, payment reference FINAL-022, authorisation reference AUTH-022.
- **E04 (09:20, internal procedure view from card operations):** Card servicing procedure — card operations can investigate a lingering linked authorisation following a completed purchase and release an eligible stale hold after checking linkage and current network state; the case desk may request investigation but cannot release a hold; release timing depends on those checks.
- **E05 (09:25, chat):** Customer asks for the £600 to be returned to available money today, needs groceries, and does not want "a generic answer about the hotel". No desk response is recorded (request.md).

**Authenticated records vs. customer report:** The ledger (E01) and merchant receipt (E03) are authenticated records. The claim that £1,120 was taken (E02) is the customer's reading of the available-balance figure and is contradicted by the ledger.

## 2. Evidence and gaps

**What the ledger proves (`card-entries.csv`):**
- Opening ledger £1,500.00 (booked).
- One card debit: FINAL-022, −£520.00, linked authorisation AUTH-022, **booked** 2026-11-10T08:30.
- One authorisation_reservation: AUTH-022, £600.00, status **active**, recorded 2026-11-10T09:00. This is a reservation entry, not a debit.
- Ledger balance snapshot £980.00 (1,500 − 520). Available balance snapshot £380.00 (980 − 600 reservation).

**What the receipt proves (`hotel-receipt.pdf`):** The merchant's final charge is £520.00 under the same payment reference (FINAL-022) and authorisation reference (AUTH-022) that appear in the ledger. The stay ended on 2026-11-10. This links the active hold and the booked debit to a single completed purchase.

**Reconciliation of the customer's claim:** £980 + £600 reservation = £1,580 would not match any ledger figure; the actual arithmetic is £1,500 − £520 = £980 ledger, less £600 hold = £380 available. Only £520 has left the account. The £600 is a hold, not a second charge.

**Gaps (cannot be established from the desk):**
- The current card-network state of AUTH-022 — whether the merchant has released, or will release, the authorisation. Only card operations can check this (E04).
- Card operations' eligibility determination and release timing. The ledger says "active" as of 09:00; nothing later is recorded.
- Why the hold is still active (merchant timing, network lag, etc.) is not in evidence and the plan correctly refrains from speculating.

No contradictions exist between the authenticated sources; the only discrepancy is the customer's interpretation.

## 3. Why this plan

**Step s1 — request card operations investigation.**
- *Explanation:* The ledger and receipt together show one completed £520 purchase with a still-active £600 authorisation under the same reference. This is exactly the "lingering linked authorisation following a completed purchase" that the E04 procedure addresses.
- *Evidence:* `card-entries.csv` (FINAL-022 booked, AUTH-022 active, same linkage), `hotel-receipt.pdf` (final £520, references FINAL-022/AUTH-022), `history.md` E04.
- *Decision criterion:* The case desk may request investigation; only card operations can release an eligible stale hold after linkage and network-state checks.
- *Rule source:* This is a supplied bank procedure (E04, Brackenfold Bank card operations), not a skill heuristic and not a legal obligation. It defines both the available route and the limit of desk authority.
- *Why time-sensitive:* The customer states (E05) they need the funds today for groceries. Flagging urgency is within the request; it does not change the eligibility test or timing, which remain with card operations.
- *Why pass the receipt:* It is the merchant's own confirmation of the final amount and references, which is the linkage evidence card operations need.

**Step s2 — reply to the customer.**
- *Explanation:* The customer's misunderstanding is directly answerable from the ledger and receipt. The reply must state only what the record proves (debit booked, hold active), that a release request is pending with card operations, and that same-day timing cannot be promised.
- *Evidence:* `card-entries.csv`, `hotel-receipt.pdf`, E04, E05.
- *Decision criterion:* Distinguish authorisation from debit; state only the proven stage; a release request is not a completed release; do not promise timing absent an applicable commitment.
- *Rule source:* Payments-handling skill rule (`skill:payments`) for how to describe holds versus debits and how to word pending requests. No supplied bank policy sets a release SLA, so no timing commitment can be made.
- *Ordering:* s2 requires s1 so the customer is told accurately whether the request has been raised. Because s1 has not yet been acknowledged, the draft in ANSWER.md says "I am raising"; the plan itself directs this fallback wording. A "has been raised" variant is provided in `future_messages`, conditional on s1 acknowledgement.
- *Financial support mention:* The plan includes a pointer to the bank's financial support team as a hardship route; it is an offer, not an operation, and no new product or promise is added.

**Alternatives considered and why not taken:**
- *Releasing the hold from the desk:* Not permitted under E04.
- *Telling the customer to contact the hotel:* The customer explicitly rejects a "generic answer about the hotel" (E05), and the supplied procedure gives the bank an internal route, so the plan uses it. The plan does not forbid the hotel route but does not adopt it.
- *Treating this as a dispute or fraud:* Nothing supports it — the merchant's own receipt matches the ledger debit. Speculating about merchant error or fraud is prohibited by `must_not`.

## 4. Execution boundaries

- **s1** has no prerequisites; it is a request to card operations, not a release. It stops at "request submitted"; the desk does not determine eligibility or timing.
- **s2** depends on s1 being acknowledged as sent. If s1 is not acknowledged, the present-tense draft ("I am raising") is used; if acknowledged, the `future_messages` draft ("I have raised") may be used. No other branch is created.
- The plan ends pending card operations' response. Whether AUTH-022 is released, when, and what the customer is told afterwards require a fresh decision once card operations report back. The plan does not pre-commit to any follow-up outcome.
- No escalation triggers (`escalate_if`) and no safety flags are set; identity authority is established via the recorded passed authentication (E01).

## 5. Expected result and limits

**What the steps could achieve:** Card operations receive a complete, evidence-backed request with the receipt attached and the urgency flagged; the customer receives an accurate explanation (£520 debited, £980 ledger, £600 active hold, £380 available), knows a request is being raised, knows the desk cannot release the hold and that same-day return is not guaranteed, and is offered the financial support route if hardship results.

**What remains unconfirmed:** Whether AUTH-022 is eligible for release; its current network state; when any release would reach the available balance. The customer's request for the money "today" cannot be satisfied or refused by the desk — it can only be forwarded and flagged.

**Constraint check:**
- `must_state` items are all covered in the draft message (only £520 taken / £980 ledger; £600 is a linked hold not a second charge / no £1,120; hold reduces available to £380; request to card operations raised or being raised and marked time-sensitive; desk cannot release and timing not guaranteed; customer will be updated; financial support available).
- `must_not` items are respected: no double-charge or £1,120 statement; no promise of same-day availability; no claim the hold is released or that card operations have acted; no credential requests; no speculation about merchant error or fraud.

**Confidence:** High on the factual reconciliation (two independent authenticated sources agree). Moderate-to-low on outcome timing, which is entirely outside the desk's control and evidence.
