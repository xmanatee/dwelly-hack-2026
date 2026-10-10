# Decision memo: Case 023 / dispute DB-023

The full input is saved in `context.md`. Everything below is proposed. No action has been taken.

## 1. Situation and history
- **Before the contact (authenticated records):** the purchase ORDER-023 for −£900.00 was booked on 2026-10-30. Provisional dispute credit PC-023 for £900.00 was recorded as `provisional_booked` on 2026-11-05 (`attachments/account-entries.csv`).
- **E01 (2026-11-11 09:00), internal disputes record:** DB-023 was retrieved with state `open`, a provisional £900.00 credit (PC-023) and the procedure text. The record says authentication passed for Maren Folsey (`attachments/dispute-status.json`).
- **E02 (09:10), merchant email from Cresswheel Furnishings to the customer:** the merchant agrees to refund £900 for SYN-ORDER-023, expects the card refund within three working days, and says it will send a processing reference "when available". This is the merchant's own statement. We see it only because the customer forwarded it. It is not a bank record.
- **E03 (09:15), authenticated customer chat:** the customer acknowledges that "You already put £900 in" and asks the bank to "pay the merchant refund to me now as well".
- **E04 (09:20), internal ledger view:** merchant refund total MR-023 was £0.00 at 09:20 (`attachments/account-entries.csv`).
- **E05 (09:25), customer chat:** "Please add another £900 today and close the dispute as won. If the shop pays later, that can be sorted afterwards." The desk has not replied yet (`request.md`).

## 2. Evidence and gaps
- **Facts the records establish:** the dispute is open and the provisional credit is booked (dispute-status.json, account-entries.csv). No merchant refund had posted by 09:20 (MR-023 = £0.00). Identity is established through the disputes record (E01) and the authenticated chat (E03).
- **What the customer reports:** the merchant's agreement (E02) is a promise. Nothing in the evidence shows a posting or a processing reference.
- **Gaps (from the plan's `missing`):** we do not have a posting of the merchant refund for SYN-ORDER-023 or the merchant's processing reference. We cannot tell whether or when the refund will post, or what the disputes team will decide when it reconciles.
- **Small observation:** E05 is labelled "Customer chat", while E03 is labelled "Authenticated customer chat". The plan treats identity as established for this contact on the basis of E01 and E03. The decision is a refusal and changes nothing on the account, so this difference does not affect the outcome.

## 3. Why this plan
- **s1: Decline.** The customer wants a second credit for the same £900 purchase, and a won outcome, on the strength of a merchant promise alone. The records show the provisional credit is already in place and no refund has posted. *Decision criterion:* the disputes team reconciles any posted merchant refund against the provisional credit before authorising an adjustment, and a merchant promise alone is not a posting event. *Source:* this is the procedure text in the supplied `attachments/dispute-status.json`, which is a bank record. It is not a legal obligation and not a separately supplied policy document. The decline comes first because the desk has no basis for either change.
- **s2: Refer to the disputes team.** The disputes team owns reconciliation of DB-023. If it has the merchant's commitment now, it will have it when a refund posts. The referral explicitly asks for no credit, closure or adjustment. *Criterion:* use a supplied authoritative status directly, hand reconciliation to the team the procedure names, and treat a refund promise as different from a booked credit. *Source:* the `skill:payments` handling rule, which is a skill guideline, not a bank policy. Evidence: history.md, dispute-status.json, account-entries.csv.
- **s3: Reply to the customer.** The customer needs a clear answer to both requests, based on the recorded status, without implying a won outcome or an arrival date. *Criterion:* state only the stage the record proves; a refund promise is not a booked credit; do not promise arrival times without an applicable commitment. *Source:* `skill:payments`. The reply depends on s1 and s2 so that it accurately reflects the decline and the status of the referral.
- **Alternatives:** the plan's evidence does not support posting the second £900 or closing the dispute now, so the plan does not take those options. I have added no other strategy.

## 4. Execution boundaries
- The steps run in order: s1, then s2, then s3, which requires both. The reply may say the merchant's email has been passed to the disputes team only once s2 is confirmed as executed. Until then it must say the referral is in progress.
- The plan stops at the referral and the reply. Any reconciliation or adjustment after a refund posts is for the disputes team to decide under its procedure. The plan has no `escalate_if` conditions, and none is added here.

## 5. Expected result and limits
- **What the steps could achieve:** a clear, recorded refusal; the merchant's commitment noted on DB-023 with the disputes team; and a customer who knows where things stand and is invited to send the processing reference.
- **What remains unconfirmed:** whether and when the merchant refund will post, and the outcome and timing of reconciliation.
- **The message must state:** PC-023 for £900 was booked on 2026-11-05 while DB-023 is investigated; no merchant refund had been recorded as of 09:20 on 2026-11-11; no second £900 will be added, DB-023 is not being closed as won, and the dispute remains open; a posted refund will be reconciled against the provisional credit before any adjustment because both relate to the same £900 purchase; the three working days is the merchant's estimate, not a bank commitment; the customer can send the processing reference when she receives it.
- **The message must not:** say the dispute is won, closed or resolved; say the provisional credit is final or permanent; promise refund arrival within three working days or on any date; say the merchant refund has posted or been processed; promise a reconciliation outcome, amount or timing; or say the referral is complete before s2 is confirmed.
