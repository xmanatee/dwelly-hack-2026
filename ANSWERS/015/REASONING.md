# Decision memo: Case 015, disputed first Direct Debit collection

The full input is saved in `context.md`. Event and attachment IDs below refer to it.

## 1. Situation and history

**Authenticated bank records:**
- **28 Aug 2026, 11:32:** Faster Payment HV26082811320471 of £4,980.00 to "HARROW & VALE RE LIME PROPERTY CA", ref "MOVE IN 14 GROVE". Status is Completed and the payment was "received by the beneficiary bank". The balance afterwards was £1,902.30.
  - Sources: `attachments/payment_confirmation_2026-08-28.pdf`, `attachments/statement_extract.csv`, event-001.
- **2 Sep 2026:** Direct Debit instruction LP-14GROVE-0208 for Lime Property set up through an originator invite (statement INFO line, event-001).
- **14 Sep 2026:**
  - The Direct Debit collection "H&V COLLECT / LIME PROPERTY LP-14GROVE-0208" of −£4,980.00 was paid and the balance went to −£3,077.70.
  - An "UNARRANGED OVERDRAFT DAILY FEE" of −£6.50 then took it to −£3,084.20 (`statement_extract.csv`).
  - Event-001 gives an approximate "£3,100 overdrawn", an arranged limit of £1,000, and confirms that the unarranged portion incurs a daily fee.

**Originator document (not a bank record):**
- `attachments/dd_advance_notice_2026-09-09.eml` is dated 9 Sep 2026 and addressed to t.okoye@example.net.
- It shows a first collection of £4,980.00 on 14 Sep 2026, described as "balance of your account as at 8 September", then £795.00 monthly on the 14th.
- It asks the payer to contact Lime Property before the collection date if any amount is wrong.

**Customer's account (his report, not verified):**
- In event-002 (ID&V passed), he says he paid all the move-in money by transfer two weeks ago and his rent is £795. He wants everything back today under the Guarantee and wants the Direct Debit cancelled.
- In event-004 he says he never agreed to £4,980 by Direct Debit.
- Event-001 records that he says he did not read the advance notice.

Event-003 is the agent's holding acknowledgement and contains no new facts.

## 2. Evidence and gaps

**What the records support:**
- The customer's identity and authority are established (event-002, event-001).
- The £4,980.00 transfer on 28 Aug was sent and reached the beneficiary bank. The PDF states that it is "not a receipt from the beneficiary".
- A mandate existed from 2 Sep, and the £4,980.00 collection on 14 Sep was paid.
- The advance notice announced exactly that amount.
- The account is beyond its arranged limit, and a daily fee has started.

**What cannot be established from the context:**
- **How Lime Property allocated the 28 Aug payment.** Event-001 says this explicitly. The notice describes the £4,980.00 as the "balance … as at 8 September", which is the same figure as the 28 Aug transfer. From this evidence we cannot tell whether the earlier payment was credited, misapplied, or covered something else.
- **What amount the customer agreed to when he accepted the originator invite on 2 Sep.** No originator-side mandate evidence is supplied.
- **The outcome of any Guarantee/indemnity claim.** None is recorded.

**Tensions in the evidence:**
- The notice shows the amount was announced in advance. The customer, however, denies agreeing to it and says he did not read the notice. Neither side proves agreement or its absence, so the plan treats this as something for the claims team to decide, not the servicing agent.
- The overdraft figure in event-001 ("£3,100") is a rounded summary. The statement shows −£3,077.70 after the collection and −£3,084.20 after the fee. The plan uses the statement figures.

**Not supplied:** the Direct Debit Guarantee scheme rules and any bank fee policy. The rule sources below are skill handling rules, not quoted policy or law.

## 3. Why this plan

**s1: Guarantee/indemnity claim to the Direct Debit claims team**
- **Explanation:** The customer disputes the amount of a Direct Debit collection and explicitly invokes the Guarantee. Whether the amount was an error, given the matching earlier transfer and the notice wording, needs a claims decision. The servicing agent should not guess.
- **Evidence:** event-002, event-004, event-001, the advance notice, the 28 Aug payment confirmation and the statement extract.
- **Criterion:** A Guarantee claim addresses errors in Direct Debit collection. Identify the error and the right route without promising a refund for every dispute with a supplier.
- **Source:** skill:scheduled-payments (a handling rule, not a quoted scheme clause).
- **Why first:** It is the main remedy the customer asked for, and the fee review (s3) depends on its context.

**s2: Mandate cancellation to the Direct Debit servicing team**
- **Explanation:** The verified account holder explicitly asked for the Direct Debit to be cancelled. Cancellation is kept separate from the refund claim.
- **Evidence:** event-002 and the statement extract.
- **Criterion:** Reuse the supplied mandate details and the authorisation already established. Cancelling an instruction does not show that a collected payment was reversed. Keep a Guarantee claim separate from changes to future instructions.
- **Source:** skill:scheduled-payments.
- The instruction tells the team not to record cancellation as reversing the 14 Sep collection.

**s3: Overdraft fee review to the overdraft / account servicing team**
- **Explanation:** The disputed collection pushed the account about £2,084 beyond its arranged limit, and a daily fee is already being charged. That fee impact needs a decision now, without assuming how the claim will end.
- **Evidence:** the statement extract, event-001 and event-002.
- **Criterion:** Keep the confirmed stage separate from the outcome. A review request does not establish a fee reversal.
- **Source:** skill:complaints-rights.

**s4: Reply to the customer on the call**
- **Explanation:** The reply covers both of his requests and reports only what the records prove. It keeps every proposed operation pending and asks for the one missing fact: how the agency allocated the 28 Aug payment.
- **Evidence:** event-002, event-004, the payment confirmation, the advance notice and event-001.
- **Criterion:** State only the stage the supplied record proves. A payer's claim about a payment is not evidence that the payee booked it as a credit. Do not promise arrival times or outcomes without an applicable commitment.
- **Source:** skill:payments.

**Alternatives not chosen:**
- **Refunding immediately at the agent's discretion:** the plan does not support this, and the must_not rules forbid promising a same-day refund.
- **Declining the claim because of the advance notice:** this would mean deciding the agreement question, which the evidence cannot settle and the plan forbids.

No safety flags or escalation triggers are recorded in the plan.

## 4. Execution boundaries

- s1, s2 and s3 are independent team requests. None has a recorded `requires` or condition. s4 is said on the current call and describes s1 to s3 as being submitted.
- Nothing has been executed. No claim reference, cancellation confirmation or fee decision exists yet.
- The plan stops at:
  - the claims team's decision;
  - recording the mandate cancellation;
  - the overdraft team's decision on fees;
  - the customer providing Lime Property's statement of account.
- Any outcome from those teams, or a team being unable to act, needs a fresh decision. This memo does not set out further branches.

## 5. Expected result and limits

**What the steps could achieve:**
- A recorded Guarantee/indemnity claim with a reference.
- Future collections under LP-14GROVE-0208 stopped.
- A fee-treatment decision for the period while the claim is pending.
- Evidence about how the 28 Aug payment was allocated, if the customer obtains the statement.

**What remains unconfirmed:**
- Any refund of the £4,980.00, or its timing.
- Any fee reversal.
- Whether the Guarantee applies.
- How Lime Property applied the 28 Aug payment.

**The customer message must state:**
- A Guarantee/indemnity claim for the £4,980.00 is being raised and its outcome is undecided.
- Cancellation is being requested. It stops future collections only and does not reverse the 14 Sep collection.
- Once cancelled, the £795 monthly rent will no longer be collected by this Direct Debit, so he must arrange another way to pay it with Lime Property.
- A fee review is being requested and no outcome is confirmed.
- The 28 Aug payment was sent and received by the beneficiary bank, but we cannot see how Lime Property applied it.
- He should ask Lime Property for a statement of account showing how that payment was allocated.

**The customer message must not:**
- Promise a refund (today or at all), or give an unsupported timescale.
- Say the Guarantee definitely does or does not apply.
- Say the notice proves agreement, or proves the lack of it.
- Say how the agency received, allocated or misapplied the 28 Aug payment beyond what the confirmation shows.
- Say anything has been cancelled, registered or refunded before execution is acknowledged.
- Say cancelling the Direct Debit ends his tenancy obligations or clears any amount owed to Lime Property.
- Ask for PINs, passwords or one-time codes.
