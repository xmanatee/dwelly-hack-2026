# REASONING — Case 019: Duplicate payment to a cleaner

Full input is preserved in `context.md`. This memo sets out the public grounds for the plan of record.

## 1. Situation and history

**Authenticated bank records**

- `attachments/payment_confirmation_2026-08-12.pdf` (Harrow & Vale Bank plc): Faster Payment **HV26081210144802**, 12 Aug 2026 10:14, **£651.00** to **CO-CLEAN SERVICES LTD**, reference "INV 4471 53 WINCHESTER", status **Completed**, "sent from your account and received by the beneficiary bank". The document itself notes it is a confirmation of payment, not a receipt from the beneficiary.
- **event-001** (internal account view, 23 Sep 2026): the only listed entry is the 12 Aug debit of −£651.00 to CO-CLEAN SERVICES LTD, flagged as a new payee with a **CoP match at the time**. The note also records the customer's own account of events (agency paid on 15 Aug; Co-Clean agreed a refund on 17 Sep).

**Customer's report and customer-supplied documents**

- **event-002 / request.md** (23 Sep, in-app chat): Linda Ferris says she paid the end-of-tenancy cleaner £651 on 12 Aug, her letting agent paid the same invoice from her rent, Co-Clean agreed to refund one payment "but it's been a week", and asks the bank to recall the payment "so I get it back faster".
- **event-003**: the agent replied that they would look at the payment and explain what a recall would and wouldn't do.
- **event-004**: the customer pushes back — "It was a duplicate payment, isn't that exactly what recalls are for?"
- `attachments/agency_statement_extract.txt`: an extract from the Oakfield PM landlord statement showing a contractor payment to Co-Clean Services Ltd, inv 4471, −£651.00 on 15/08/2026. Supplied by the customer; not a bank record.
- `attachments/coclean_refund_agreement.eml` (17 Sep 2026, from accounts@co-clean.example): Co-Clean acknowledges receiving £651 from the customer on 12 Aug and another £651 from Oakfield PM on 15 Aug against invoice 4471, and states "We'll refund £651 to you on our next payment run." No date for that run is given.

Identity/authority is recorded as established. No safety flags are raised.

## 2. Evidence and gaps

**What is established by bank records**

- The 12 Aug payment was initiated from the customer's account, to the payee she set up, with a name-check match, and reached the beneficiary bank with status Completed (`payment_confirmation_2026-08-12.pdf`, event-001). Nothing in the bank record indicates a processing fault, misdirection, or a second debit from this account.

**What rests on third-party or customer-supplied material**

- That Oakfield PM also paid invoice 4471 on 15 Aug comes only from the customer-supplied statement extract and Co-Clean's email. Both are consistent with each other and with the customer's account, but they are not Harrow & Vale records, and the plan treats them as third-party facts rather than bank findings.
- That Co-Clean has agreed to refund is evidenced by the forwarded email. It is an agreement to pay, not a booked credit.

**Gaps (as listed in the plan's `missing`)**

- No bank procedure or policy for funds-return requests on authorised, correctly-addressed Faster Payments was supplied. The plan does not assume one, and neither the answer nor this memo cites any clause or scheme rule.
- The date of Co-Clean's "next payment run" is unknown, and the 23 Sep snapshot (event-001) does not show whether a refund credit has since arrived. Absence from the snapshot is not evidence that no refund has been made.
- Whether invoice 4471 covered exactly the same service and amount in both payments is supported only by the extract and Co-Clean's email.

**No contradictions** were found between the customer's account and the documents; the issue is one of characterisation (the customer treats the situation as a "duplicate" that the bank can reverse) rather than disputed facts.

## 3. Why this plan

### s1 — Hold/decline the recall (`skill:payments`)

- **Explanation (from the plan):** the confirmation proves a completed, correctly-addressed, authorised payment. Nothing in the evidence shows a bank-side duplicate or misdirection that a recall would address, and the payee has already agreed to refund directly.
- **Evidence:** `payment_confirmation_2026-08-12.pdf`, `coclean_refund_agreement.eml`, event-001, event-004.
- **Criterion:** use the supplied authoritative status directly; a recall/return request is not a completed return, and similar transfers are not automatically bank duplicates.
- **Source:** this is the payments skill's handling rule. It is **not** a cited bank policy or legal obligation — none was supplied — and the plan expressly lists the absence of a bank funds-return procedure as a gap.

Why this follows from the evidence: the customer's framing (event-004) is that a duplicate is "exactly what recalls are for". The record shows that the 12 Aug payment was not duplicated by the bank — there is one debit, correctly addressed with a CoP match, received by the beneficiary bank. The second payment was made by a different payer (Oakfield PM) from a different source (rental funds held by the agency) on a different date (15 Aug). A recall for the 12 Aug payment would therefore be a request to Co-Clean's bank to return a correctly made payment, which in practice turns on the recipient's agreement — the same recipient that has already agreed in writing to refund. On the supplied evidence there is no demonstrated speed or success advantage, so the plan declines rather than raising a request whose outcome cannot be promised.

**Alternative considered within the plan's bounds:** raising the recall anyway "to try". The plan rejects this because it cannot be presented to the customer as faster or likely to succeed without evidence, and doing so could divert her from the concrete step (chasing Co-Clean for the payment-run date) that the record supports. No other strategy is added here.

### s2 — Reply to the customer (`skill:payments`)

- **Explanation (from the plan):** answers the customer's direct question about recalls with only the stages the record proves, keeps the agency payment and Co-Clean's refund agreement as third-party facts, and avoids promising speed or outcome.
- **Evidence:** event-004, `payment_confirmation_2026-08-12.pdf`, `coclean_refund_agreement.eml`, `agency_statement_extract.txt`, event-003.
- **Criterion:** state only the payment stage the supplied record proves; do not promise arrival times or treat a refund agreement as a booked credit.
- **Source:** payments skill handling rule.

The message fulfils the commitment made in event-003 (explain what a recall would and wouldn't do), covers each `must_state` item — authorised/CoP match/Completed and received; recall is a request not a reversal and depends on the recipient; duplicate arose from Oakfield PM's 15 Aug payment, not a bank error; Co-Clean's 17 Sep agreement gives no date and the bank has not confirmed arrival; next step is to ask Co-Clean for the run date and reference and return if it does not arrive — and avoids every `must_not` item (no recall claimed, no refund-received claim or date, no "bank error" wording, no policy clause cited, no suggestion the agency payment is disputable through this bank, no promised outcome or timescale).

**Order:** s2 requires s1 so that the decision not to raise a recall is recorded before the customer is told it is not being raised.

## 4. Execution boundaries

- **s1** is a record-only decision for the servicing agent/case record. It changes nothing on the account.
- **s2** is a single in-app chat reply, dependent on s1 being recorded first.
- The plan **stops** after s2. It does not raise a recall, does not open a dispute, does not contact Co-Clean or Oakfield PM, and does not set any follow-up date. The customer is invited to come back if the refund does not arrive; what happens then is not decided here and would need a fresh decision on new information (e.g. the payment-run date, a non-arrival, or a bank funds-return procedure being supplied).
- There are no `escalate_if` conditions and no conditional branches in the plan.
- Nothing has been executed at the time of this memo.

## 5. Expected result and limits

**What the proposed steps could achieve:** a recorded, reasoned decision not to raise a recall, and a clear explanation to the customer of why, with a practical next step she can take with Co-Clean. Expected disposition: completed.

**What remains unconfirmed:**
- Whether Co-Clean's refund has already been credited, or when its next payment run is.
- Whether a recall request, if one were raised, would be accepted — this cannot be known and is not promised either way.
- The bank's own procedure for funds-return requests on authorised, correctly-addressed payments, which was not supplied and is therefore neither relied on nor cited.

**Constraints carried through:** every `must_state` point appears in the customer message; none of the `must_not` items is breached. The 12 Aug payment is consistently described as an authorised, correctly addressed, completed payment, and the Oakfield PM payment as a separate third-party transaction outside this bank. No amounts, dates, references or outcomes beyond those in the plan and context have been introduced.
