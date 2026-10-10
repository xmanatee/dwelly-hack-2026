## 1. Situation and history

Gabriela Petrova, personal current account holder (no arranged overdraft), called personal banking on 25 Sep 2026 and passed ID&V (event-002). Her report: she moved out of 78 Coombe Road at the end of August; Oakfield PM collected £875 on 23 Sep, putting her overdrawn; a £2,525 collection is due Monday 28 Sep; the agency told her it is "already submitted" and cannot be cancelled on their side; she has £600 available. In event-004 she demands refunds of the August and September collections, a stop on Monday's collection, and reversal of the overdraft fee, which she says is not her fault.

Authenticated bank records (event-001, `attachments/statement_extract.csv`, `attachments/incoming_dd_instruction.json`):
- Mandate H&V COLLECT / OAKFIELD PM, ref OPM-78COOMBE-3312, active since Feb 2025, monthly.
- 24 Aug 2026: DD −£875.00 (balance £1,204.60).
- 23 Sep 2026: DD −£875.00, balance −£412.90.
- 24 Sep 2026: unarranged overdraft daily fee −£6.50, balance −£419.40.
- 25 Sep 2026: transfer from savings +£1,019.40, balance £600.00.
- Incoming instruction: £2,525.00, collection date 2026-09-28, received by bank 2026-09-24T02:10:44Z, status "scheduled", narrative "FINAL ACCOUNT 78 COOMBE RD".

Customer-supplied document (`attachments/agency_move_out_confirmation.eml`): email from Oakfield PM dated 1 Sep 2026 confirming the tenancy ended 31 Aug 2026, with check-out report and deposit to follow. This was forwarded by the customer; it is the originator's own statement but has not been independently verified by the bank.

The agency's remark that it cannot cancel the collection is customer-reported (event-002), not a bank record.

## 2. Evidence and gaps

Established from records: identity and account ownership (event-002, event-001); the three collections and the fee (statement extract); the scheduled instruction and its receipt time (instruction JSON); the available balance of £600 being below the £2,525 due (event-001, statement).

Supported by the originator's own document: tenancy end 31 Aug 2026 (agency email), which places the 23 Sep collection after the tenancy end and the 24 Aug collection within it.

Cannot be established from the visible context (see `context.md` for the full input):
- Whether Oakfield PM sent advance notices for the 23 Sep or 28 Sep collections, and whether any notice matched the amounts and dates (event-001 states the bank cannot see this; the customer has not yet said).
- Whether the 28 Sep collection can still be stopped or is already in flight — the payments team must report this.
- Any specific error alleged in the 24 Aug collection; the customer's demand (event-004) does not identify one.
- What the £2,525 "final account" comprises — a matter between customer and agency, not visible to the bank.
- Outcomes of the indemnity claim and complaint, including any fee decision.

No contradictions between the customer's account and the records were found; the records corroborate the dates and amounts she cites.

## 3. Why this plan

**s1 — Cancel mandate and attempt stop of 28 Sep collection.** The verified payer has explicitly instructed that Monday's collection be stopped (event-002, event-004). Under the scheduled-payments handling rule applied by the plan, a payer may cancel a Direct Debit with their bank, but a collection instruction already received (24 Sep) may be in flight, so a stop is requested and its outcome reported rather than promised. This is a skill handling rule, not a cited bank policy or statutory provision.

**s2 — Ask about advance notices.** Whether advance notice was given, and whether it matched the collection, is the key error basis under the Guarantee for both September collections, and only the customer can tell us (event-001, event-002). The handling rule requires a Guarantee claim to identify the error rather than treat every supplier dispute as refundable.

**s3 — Indemnity claim for 23 Sep £875.** The collection post-dates the tenancy end confirmed by the originator's own email, giving a specific, evidenced basis (statement extract, agency email, event-004). The claims team assesses eligibility; the plan does not decide it and no refund is confirmed. The handling rule keeps the claim on a collected payment separate from cancelling future instructions.

**s4 — Decline claim for 24 Aug £875 on current evidence.** It falls within the tenancy period, matches the established monthly pattern since Feb 2025, and no error in amount, date or notice has been identified. The Guarantee addresses setup/collection errors, not disputes over sums that appear contractually due. The customer is told she can identify a specific error for review — the decline is on current evidence, not final.

**s5 — Register complaint.** The customer expresses dissatisfaction and seeks redress including fee reversal (event-004). The complaints handling rule treats this as a complaint to be registered and reviewed separately from operational work; a review request does not establish fee reversal or compensation. The safety flag `complaint_rights` is satisfied by registering the complaint and informing her of the Financial Ombudsman Service route, without quoting a fixed response deadline.

**s6 — Reply.** The customer needs the recorded position on each of her four requests, what remains unconfirmed, and the single fact needed from her.

Alternatives considered within the plan's scope: raising a Guarantee claim for the August collection was rejected because no error is identified; promising a stop of Monday's collection was rejected because the instruction is already received. No further strategy is added here.

## 4. Execution boundaries

- s1, s2, s3, s4 and s5 have no execution dependencies and can be raised in parallel during the call.
- s6 requires s1, s3 and s5 to have been actioned; the plan's s6 wording ("I've requested…", "I've asked…") describes requests as already made, so it is returned separately as a future message, NOT SENT, pending acknowledgement of those steps. The answer contains a present-state version in pending language covering the same must_state points and the s2 question.
- The plan stops pending: the payments team's report on whether the 28 Sep collection was stopped; the customer's answer on advance notices; the indemnity claim outcome; the complaint outcome including the fee decision. If the 28 Sep collection debits despite s1, the plan records that a further Guarantee claim can be raised — this is noted in s3, not executed now. Any blocked step (e.g. the collection cannot be stopped) requires a fresh decision rather than an improvised alternative.

## 5. Expected result and limits

What the steps could achieve: the mandate cancelled so no further Oakfield PM collections are taken; a possible stop of the £2,525 collection; assessment of the 23 Sep £875 under the Guarantee; a registered complaint with a reference, within which the £6.50 fee is considered; and a clear record of what the customer was told.

What remains unconfirmed: whether Monday's collection will actually be stopped; whether either September amount will be refunded; whether the fee will be reversed; whether advance notices were sent; and whether any sum is owed to Oakfield PM on its final account, which cancelling the mandate does not settle.

Constraints preserved: all must_state points appear in the customer message; no stop, refund or fee reversal is promised; the August collection is not described as an error or refunded; the bank does not assert whether notices were sent; no complaint deadline or Ombudsman outcome is quoted; and all team actions are described as proposed, not executed.
