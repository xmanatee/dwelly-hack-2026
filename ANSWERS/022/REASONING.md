## 1. Situation and history

All events are on 2026-11-10, case 022, account SYN-ACCT-B022. The full input is in the saved `context.md`.

- **E01 (09:00), internal card view:** The card ledger entries were retrieved, with attachment `attachments/card-entries.csv`. The account holder is Rois Fenwick, and current contact authentication is recorded as passed.
- **E02 (09:10), authenticated chat:** The customer says the hotel took £600 and £520 (£1,120), that her available balance is only £380, and that she thought the stay cost £520. **This is the customer's own account of events.**
- **E03 (09:15), merchant email with bank support copied:** Alderclock Hotel sends the final receipt `attachments/hotel-receipt.pdf` and says the final card amount is £520.
- **E04 (09:20), internal procedure view from card operations:**
  - Card operations can investigate a lingering linked authorisation after a completed purchase.
  - They can release an eligible stale hold after checking linkage and current network state.
  - The case desk may request an investigation but cannot release a hold itself.
  - Release timing depends on those checks.
- **E05 (09:25), customer chat:** She asks for the £600 to be back in her available money today because she needs groceries, and she does not want a generic answer.
- `request.md` records that the desk has not yet responded to the final request.

## 2. Evidence and gaps

**What the authenticated bank records show (`card-entries.csv`):**
- Opening ledger balance: £1,500.00.
- One booked `card_debit`: FINAL-022, −£520.00, at 08:30, linked to AUTH-022.
- One `authorisation_reservation`: AUTH-022, £600.00, status **active**, recorded at 09:00.
- Snapshot at 09:00: ledger balance £980.00 and available balance £380.00.
- The figures reconcile: £1,500 − £520 = £980, and £980 − £600 = £380. So the £600 lowers the available balance but is **not** a booked debit.

**What the merchant document shows (`hotel-receipt.pdf`, SYN-HOTEL-022):**
- Stay from 2026-11-07 to 2026-11-10, issued at 09:10.
- Final amount paid by card: GBP 520.00.
- Payment reference FINAL-022 and authorisation reference AUTH-022.
- This matches the ledger and supports the view that the £600 is a hold linked to the completed £520 purchase.

**The contradiction:** The customer says she was charged twice (E02). The ledger and receipt show one debit and one reservation. The plan relies on the records.

**Gaps that cannot be resolved from the supplied material:**
- Whether AUTH-022 is actually eligible for release. That depends on card operations checking the linkage and the current network state (E04), and no result has been supplied.
- When any release would take effect. No timing commitment was supplied.
- Any balance data after the 09:00 snapshot. The reservation may have changed since then, but we cannot tell.
- The reservation row is timestamped 09:00, which is after the 08:30 debit. This may simply be the snapshot time. It does not change the plan, but it is a reason not to call the hold "stale" before card operations checks it.

## 3. Why this plan

**s1: Request card operations action**
- **Explanation:** The £600 reservation shares its authorisation reference with a completed £520 purchase and with the hotel's final receipt. That matches the "lingering linked authorisation" described in E04. The case desk can ask for an investigation but cannot release the hold.
- **Evidence:** `card-entries.csv`, `hotel-receipt.pdf`, `history.md` (E04).
- **Criterion:** The case desk may request investigation of a lingering linked authorisation after a completed purchase. Only card operations can release an eligible stale hold, after checking linkage and network state.
- **Rule source:** `evidence:history.md`. This is the card servicing procedure supplied in E04. It is a bank procedure shown in the case evidence, not a legal obligation.
- **Why it comes first:** It is the only route in the supplied material that could lead to the £600 being released. The same-day grocery need (E05) is passed on as a priority request, conditional on card operations' procedure, and not as a commitment.

**s2: Reply to the customer**
- **Explanation:** The customer believes she was charged £1,120. The ledger and receipt directly show one £520 debit and one £600 reservation. She needs a specific, accurate answer about the hold and how release works, not a generic answer or a promised time.
- **Evidence:** `card-entries.csv`, `hotel-receipt.pdf`, `history.md`.
- **Criterion:** State only the stage the records prove, keep the reservation separate from the booked debit, and do not promise a release time without an applicable commitment.
- **Rule source:** `skill:payments`. This is a handling rule from the payments skill, not a bank policy or legal requirement supplied in the case.
- **Why it depends on s1:** The message refers to the card operations request. It may only say the request "has been sent" once card operations acknowledges s1. Before that, it must say the request is being raised. The pre-acknowledgement version is in ANSWER.md, and the post-acknowledgement version is drafted separately as NOT SENT.

**Alternatives:** A desk-side release is not available, because E04 says the case desk cannot release a hold. A refund or merchant dispute is not supported, because the hotel's figures match the ledger and there is no evidence of a merchant error.

## 4. Execution boundaries

- **s1** has no preconditions. Identity authority is established through the passed authentication (E01) and the authenticated chat (E02).
- **s2** depends on s1 being raised, and its wording depends on whether card operations has acknowledged s1.
- The plan stops after these two steps. Whether the hold is released, and when, is up to card operations. Their outcome needs a fresh decision on the case and is not decided here.
- The plan has no `escalate_if` conditions and no safety flags.

## 5. Expected result and limits

**What the proposed steps could achieve:**
- The customer gets an accurate explanation: one £520 payment, plus a £600 hold with the same reference AUTH-022 as the payment and the receipt.
- She sees her balances as of 09:00 (£980 ledger, £380 available) and knows the £380 can be used now.
- She knows a check by card operations has been requested.

**What remains unconfirmed:**
- Whether the hold is eligible for release.
- When any release would happen.
- Any balance after 09:00.

**The customer message must state:**
- There was one £520 payment (FINAL-022), and the £600 is a pending hold, not a second charge.
- The 09:00 balances were £980 ledger and £380 available, because of the hold.
- The hold has the same reference AUTH-022 as the payment and the receipt.
- The case desk cannot release the hold, card operations must check it, and the timing depends on those checks.
- We cannot promise the money will be available today.
- The £380 can still be used.

**The customer message must not:**
- Say the £600 was charged or debited, or that it was a second payment.
- Promise a release today or by any specific time.
- Say the hold has been released or that the investigation is finished.
- Call the hold stale or eligible before card operations has checked it.
- Say the request has been sent before card operations acknowledges it.
- Say the hotel made an error or that a refund is due.
- Ask for a PIN, password or one-time code.
