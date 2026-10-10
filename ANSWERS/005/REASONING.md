# Reasoning memo: Case 005, Oakfield Direct Debit after move-out

The full input is saved in `context.md`. Every step in this memo is **proposed or pending**. The plan is an escalation to three teams, plus a question and a reply to the customer on the current call.

## 1. Situation and history

**Authenticated bank records**
- **event-001** (internal account view, 25 Sep 2026): Gabriela Petrova has a personal current account with no arranged overdraft.
  - Mandate H&V COLLECT / OAKFIELD PM has been active since Feb 2025 and collects monthly.
  - Collections: £875 on 24 Aug and £875 on 23 Sep. After the 23 Sep collection the account was overdrawn and a £6.50 unarranged overdraft fee was applied on 24 Sep.
  - A £2,525 collection is scheduled for Mon 28 Sep. The instruction was received from the originator on 24 Sep.
  - A £1,019.40 transfer from savings posted on 25 Sep, leaving £600.00 available.
  - The bank cannot see whether advance notices were sent.
- **attachments/statement_extract.csv**:
  - 24 Aug: DD of −875.00 (ref OPM-78COOMBE-3312)
  - 23 Sep: DD of −875.00, balance −412.90
  - 24 Sep: fee of −6.50, balance −419.40
  - 25 Sep: credit of +1,019.40, balance 600.00
  - It also shows a 1 Sep debit "NEW TENANCY RENT" of −1,052.50.
- **attachments/incoming_dd_instruction.json**:
  - Originator: Oakfield Property Management Ltd, SUN H&V COLLECT 771902, mandate OPM-78COOMBE-3312
  - Amount: £2,525.00, collection date 2026-09-28
  - Received: 2026-09-24T02:10:44Z
  - Status: "scheduled"
  - Narrative: "FINAL ACCOUNT 78 COOMBE RD"

**What the customer says or supplied**
- **event-002** (phone, ID&V passed): she moved out at the end of August. She says the agency told her the collection was "already submitted" and could not be cancelled their side.
- **event-004**: she wants both £875 collections refunded, Monday's collection stopped and the fee refunded ("it's not my fault").
- **attachments/agency_move_out_confirmation.eml**: an email from Oakfield dated 1 Sep 2026, forwarded by the customer. It confirms the tenancy at 78 Coombe Road ended on 31 Aug 2026. It says the check-out report would follow within 10 working days and the deposit would be dealt with after that. The bank has not independently verified this email, but it supports the tenancy end date the customer gives in event-001.
- **event-003**: the agent acknowledged her and said they would look at the mandate. No action was taken.

## 2. Evidence and gaps

**Established by the records**
- ID&V: event-002.
- Mandate details: event-001 and the instruction JSON.
- Both £875 collections and the fee: the statement extract.
- The £2,525 collection is scheduled and the instruction is already with the bank: the instruction JSON.
- £600 is available: event-001 and the statement.

**Minor inconsistency.** Event-001 says the account went "£412 overdrawn". The statement shows −£412.90. The plan uses the statement figure.

**Not known or not established (from the plan's `missing` list)**
- Whether the 28 Sep collection can still be stopped once the mandate is cancelled, given the instruction is already with the bank.
- Whether Oakfield sent advance notices for the 23 Sep and 28 Sep collections, and when.
- Which rent period each £875 collection covered. The 24 Aug collection came before the 31 Aug tenancy end.
- What the £2,525 "final account" is made up of. On 1 Sep the check-out report and deposit were still pending.
- The outcome of the Guarantee assessment and of the fee complaint.

Because of these gaps, nothing in the case lets the agent decide on a refund now.

## 3. Why this plan

**s1: Cancel the mandate and try to stop the 28 Sep collection (Direct Debit operations)**
- **Why:** the verified customer asked for Monday's collection to be stopped after her tenancy ended on 31 Aug. The instruction is already with the bank and marked "scheduled", so whether it can be stopped has to be confirmed, not assumed.
- **Evidence:** event-002, event-004, the instruction JSON, the agency email.
- **Criterion:** a verified payer may cancel a Direct Debit at the bank. Collections already in process may not be stoppable, so cancellation must not be promised.
- **Source:** skill handling rule `skill:scheduled-payments`. This is an internal handling rule, not a supplied bank policy or a quoted legal clause.

**s2: Direct Debit Guarantee claim for both £875 collections (Guarantee / indemnity claims team)**
- **Why:** she asks for both refunds.
  - The 23 Sep collection came after the confirmed tenancy end, and advance notice is unknown.
  - The 24 Aug collection came during the tenancy, and the records so far show no error.
  - Both should be assessed by the team, not decided on the call.
- **Evidence:** event-001, event-004, the statement extract, the agency email.
- **Criterion:** the Guarantee covers errors in Direct Debit set-up or collection. It must be kept separate from cancelling future collections. A refund must not be promised for every dispute with a supplier.
- **Source:** `skill:scheduled-payments` (skill rule).

**s3: Complaint about the £6.50 fee (Complaints team)**
- **Why:** the customer is unhappy with a bank fee and wants it refunded. That is a complaint seeking redress, so it should be handled separately from the Direct Debit work.
- **Evidence:** event-004, the statement extract, event-001.
- **Criterion:** register the complaint as its own piece of work alongside the operational query, and do not promise redress before review.
- **Source:** `skill:complaints-rights` (skill rule). The plan also flags `complaint_rights` as a safety flag.

**s4: Ask about advance notices**
- **Why:** the bank cannot see whether advance notices were sent (event-001), and this fact matters for the Guarantee assessment.
- **Criterion:** ask the customer for the specific missing fact that affects the decision.
- **Source:** `general:evidence`.

**s5: Status reply to the customer**
- **Why:** she needs to know what is being done for each of her four requests and that no outcome is confirmed yet.
- **Evidence:** event-001, event-002, event-004, the instruction JSON.
- **Criterion:** give the current status and say clearly what it does not confirm. Do not promise completion or outcomes.
- **Source:** `general:planner`.

**Why this order**
- s1 comes first because the 28 Sep collection is the most time-sensitive item, and the £2,525 is more than the £600 available.
- s2 and s3 run alongside s1 and are kept separate from it: cancelling future collections, the Guarantee claim and the complaint are three different processes under the cited skill rules.
- s4 gathers the evidence s2 needs.
- s5 tells the customer the status of everything above.

Identity and authority are established (event-002), so no further authorisation step is needed.

## 4. Execution boundaries

- **Dependencies:** none of s1–s5 has a `requires` dependency or a condition. The plan has no `escalate_if` branches.
- **Where the plan stops:** each team request is pending until that team reports back:
  - s1: whether the mandate is cancelled and whether the 28 Sep collection was stopped or remains in process
  - s2: the Guarantee assessment outcome
  - s3: the complaint outcome
- **What is not decided here:** the plan does not decide what happens if the collection cannot be stopped, or what follows from the customer's answer to s4. Those need a fresh decision once the information arrives. This memo does not add new branches.

## 5. Expected result and limits

**What the steps could achieve:** the mandate cancelled, possibly the 28 Sep collection stopped, a Guarantee assessment of both £875 collections, a registered fee complaint, and the customer's evidence about advance notices.

**What remains unconfirmed:** whether the collection will be stopped, and whether any refund (£875 ×2 or £6.50) will be paid.

**The customer message must state:**
- The mandate cancellation and the attempt to stop the £2,525 collection have been requested but are not confirmed. The instruction was received on 24 Sep, so stopping it is not guaranteed.
- Cancelling the Direct Debit does not settle or cancel any amount Oakfield says she owes. Any dispute about the "final account" is between her and Oakfield.
- Both £875 collections are being logged as a Guarantee claim for assessment. The Guarantee covers errors such as a wrong amount, wrong date or missing advance notice, and any refund depends on the assessment.
- Her £6.50 fee complaint is being registered and its outcome is not yet known.
- If the £2,525 collection goes out, it would be more than her £600 available balance.

**The customer message must not:**
- promise the 28 Sep collection will be stopped
- promise or confirm any refund
- say Oakfield failed to send advance notice (the bank cannot see this)
- say cancelling the mandate ends any debt to Oakfield
- say any team action has been completed
- give a fixed deadline or callback time
