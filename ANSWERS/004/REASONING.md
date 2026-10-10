# REASONING.md — Case 004: Two rent payments in one month

Full input is saved in `context.md`. This memo sets out the public grounds for the plan of record; nothing described here has been executed.

## 1. Situation and history

**Authenticated records (bank side):**

- **event-001** (internal account view, 4 Sep 2026) and `attachments/statement_extract_sep.csv`: on 1 Sep 2026 a standing order of £1,000.00 to HARROW & VALE RE HARBOUR LETS LTD CA, ref "RENT 27 ELM RD", debited (balance £1,642.18 after); on 3 Sep 2026 a Direct Debit of £900.00 to H&V COLLECT / HARBOUR LETS, ref HL-27ELM-0091, debited (balance £742.18 after).
- `attachments/standing_order_on_file.json`: the standing order was created 2025-02-01 by the customer, is monthly, status active, next payment 2026-10-01.
- **event-001** records the Direct Debit mandate as "created 20 Aug 2026 via originator invite".
- `attachments/dd_advance_notice_2026-08-24.eml` (originator copy visible to the bank): dated Mon 24 Aug 2026, addressed to priya.desai@example.net, states "You have set up a Direct Debit to Harbour Lets Ltd (reference HL-27ELM-0091)", first collection £900.00 on or around 3 Sep 2026 then £900.00 monthly, and asks the customer to cancel any rent standing order before the first collection "to avoid paying twice". It states the Direct Debit Guarantee applies.
- **event-001** notes the collection amount matches the notice and the standing order is still active for 1 Oct.

**Customer's report (in-app chat, authenticated personal banking session, 4 Sep 2026):**

- **event-002**: rent "taken twice" — £1,000 on the 1st, £900 on the 3rd; demands the £900 refunded under the Direct Debit Guarantee today and the Direct Debit cancelled; "I never agreed to £900, my rent is £1,000 — they've got the amount wrong."
- **event-003**: the agent confirms both payments are visible and offers to explain options.
- **event-004**: the customer rejects options, asserts the Guarantee requires an immediate refund where there is an error, and states "This is an error."

Identity authority is recorded as established (authenticated in-app chat matched to the internal view for Priya Desai; event-001, event-002, request.md). No refund, cancellation or complaint has been recorded as executed (event-003 is an acknowledgement only).

## 2. Evidence and gaps

**What the records establish**

- Two debits to the same landlord in September totalling £1,900 (statement extract; event-001).
- The £1,000 debit was the customer's own standing order, set up Feb 2025 and never cancelled (`standing_order_on_file.json`).
- The £900 debit matched the 24 Aug advance notice in amount and timing (notice .eml; event-001). The notice itself warned about paying twice if the standing order was kept.

**Contradictions and what cannot be established**

- The customer says she "never agreed to £900". The bank record says the mandate was created 20 Aug 2026 "via originator invite", and the notice is addressed to her and says "You have set up a Direct Debit". These point to a mandate accepted by her, but the supplied records do not show *who* actioned the invite or whether she saw the £900 figure. Her statement is ambiguous between (a) an unauthorised mandate and (b) an authorised mandate with an amount she disputes with her landlord. Those two cases take different indemnity routes. This is the central gap and the reason for s2.
- Whether she actually received the 24 Aug email at priya.desai@example.net is not known; the bank holds only the originator's copy.
- She has given no instruction about the £1,000 standing order due 1 Oct; the plan does not infer one.
- Whether a Guarantee error exists is a determination for the indemnity/disputes team; it has not been made.
- The customer's claim that "the amount is wrong" is a dispute about what rent is owed, which is between her and Harbour Lets; the bank records cannot settle it.

## 3. Why this plan

**s1 — hold/decline same-day refund.** The Guarantee addresses errors in the setup or collection of a Direct Debit. On record the collection matched the advance notice (event-001, notice .eml), so no error is identified; the duplication arose because the customer's own standing order remained active. The plan's criterion (source: `skill:scheduled-payments` — a handling rule, not a supplied bank policy or statute) is to identify the error and route the claim without promising a refund for every dispute, and without issuing an automatic eligibility verdict. Hence the bank neither pays today nor gives a final refusal (event-004 shows the customer expects a verdict; the plan deliberately avoids one).

**s2 — one question to the customer.** Her phrase "never agreed to £900" (event-002) against the bank's "created via originator invite" (event-001) leaves open whether this is an unauthorised mandate or an amount dispute. Criterion: request the precise missing fact when a gap changes the decision (source: `general:evidence`). The question is asked now because the indemnity team's route depends on it.

**s3 — refer to the DD indemnity / payment disputes team.** The customer has made an express Guarantee claim (event-002, event-004). The records point against a collection error, but the plan's rule is to keep the Guarantee claim separate from changes to future instructions and route it to the applicable process (source: `skill:scheduled-payments`). The referral is to pass the full factual picture — mandate date, notice date and content, matched collection, the customer's assertion, and the £1,000 standing order — so the team can determine whether an error exists and record the outcome. The chat does not pre-empt that determination.

**s4 — secure confirmation to cancel the Direct Debit.** The customer explicitly asked for cancellation (event-002). The session is authenticated, the mandate is identified (HL-27ELM-0091), nothing is in flight and the next collection is indicated on or around 3 Oct. The plan reuses the supplied mandate state and requires only the missing authorisation (secure in-app confirmation). The confirmation text must state that cancelling does not reverse the 3 Sep £900, does not change rent owed to Harbour Lets, and does not alter the £1,000 standing order — because cancelling an instruction does not establish reversal of a collected payment or end the tenancy contract (source: `skill:scheduled-payments`). The standing order is not touched because she has not asked for that.

**s5 — log a complaint.** The customer has expressed dissatisfaction, demanded redress and rejected the agent's explanation (event-004). Under `skill:complaints-rights` (a handling rule), complaint handling runs separately from the operational query, registration is not conditional on her accepting an outcome, and only acknowledgements actually available are promised. The complaint is to be linked to the s3 assessment. The safety flag `complaint_rights` is addressed here and in the customer message (Ombudsman referral right after a final response, with no deadline or outcome predicted).

**s6 — reply to the customer.** The reply states the recorded facts, what is being referred and sent for confirmation, what remains unconfirmed, and the practical route to recover the overpayment (asking Harbour Lets to refund or credit the excess), without promising any outcome (source: `general:planner`). It depends on s1, s3, s4 and s5 because its final wording describes those actions as carried out.

**Alternatives considered within the plan's bounds.** Paying the £900 today would mean treating a collection that matched its notice as an error without assessment; refusing outright would amount to a verdict the chat is not placed to give. Cancelling the standing order unasked would substitute the bank's judgement for the customer's instruction. The plan takes neither path.

## 4. Execution boundaries

- s1, s2, s3, s4 and s5 have no execution dependencies on one another.
- s6 requires acknowledgement that s1, s3, s4 and s5 have been actioned, because its final wording speaks of the referral, the complaint log and the confirmation request as already carried out. Until then, only the present-state version in ANSWER.md may be used; the final wording is held as a NOT SENT draft in `future_messages`.
- The Direct Debit cancellation takes effect only on the customer's secure confirmation; if she does not confirm, the mandate remains active and the next collection (~3 Oct) is not prevented by this plan.
- The plan stops at: the customer's answer to the s2 question, her s4 confirmation, any instruction on the £1,000 standing order, and the indemnity team's determination. Each of those is new information requiring a fresh decision; no further branches are pre-decided here. `escalate_if` is empty.

## 5. Expected result and limits

**What the steps could achieve:** a recorded reason for not paying on chat; a properly routed Guarantee claim with the full fact pattern; a cancellation request ready for the customer's authorisation; a complaint on file preserving her rights; a customer message that covers every `must_state` item (both payments visible; what the Guarantee covers and that the collection matched the notice which also asked her to cancel the SO; claim being referred, no refund confirmed, outcome unknown; cancellation pending her confirmation and its limits; SO is her own instruction, not covered, active for 1 Oct unless she instructs; overpayment can be raised with Harbour Lets; complaint being recorded and Ombudsman route; the single 20 Aug question).

**What remains unconfirmed:** whether a Guarantee error exists (indemnity team); whether the mandate was authorised by her; whether the Direct Debit will actually be cancelled (depends on her confirmation); whether Harbour Lets will refund or credit the £900 excess (the bank cannot promise this); what she wants done with the 1 Oct standing order.

**Constraints preserved (`must_not`):** no promise or implication of a refund today or of claim success; no final verdict that the Guarantee does not apply; no claim that the DD or SO has already been cancelled; no claim the bank can reverse the £1,000 standing order; no claim Harbour Lets will refund; no complaint response deadline or Ombudsman outcome quoted; no request for PINs, passwords or one-time codes.
