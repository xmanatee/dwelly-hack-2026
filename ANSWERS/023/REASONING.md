# Case 023 — Decision memo

Full input is saved in `context.md`. This memo explains the public grounds for the refusal and the proposed next steps. Nothing has been executed.

## 1. Situation and history

Authenticated records:

- **E01 (2026-11-11 09:00, internal disputes record, `attachments/dispute-status.json`):** DB-023 is `open`, with a `provisional` credit of £900.00, reference PC-023. Authentication passed for Maren Folsey. The record also carries the disputes procedure: the disputes team reconciles any posted merchant refund against the provisional credit before authorising an adjustment; a merchant promise alone is not a posting event.
- **E04 (2026-11-11 09:20, internal ledger view, `attachments/account-entries.csv`):** account SYN-ACCT-B023 shows the £900 card purchase ORDER-023 `booked` 2026-10-30; dispute credit PC-023 +£900.00 `provisional_booked` 2026-11-05; merchant_refund_total MR-023 £0.00 `snapshot_total` at 09:20.

Customer-side reports (not bank postings):

- **E02 (09:10, merchant email, Cresswheel Furnishings to the customer):** the merchant agrees to refund £900 for SYN-ORDER-023, expects the card refund to reach the customer within three working days, and will provide a processing reference "when available". No reference is in the file.
- **E03 (09:15, authenticated chat):** the customer forwards the shop's message, acknowledges the £900 already credited during investigation, and asks the bank to pay the merchant refund to her now as well.
- **E05 (09:25, chat):** the customer asks for "another £900 today" and for the dispute to be closed as won, saying any later merchant payment "can be sorted afterwards".

Per `request.md`, no desk response to E05 is recorded; the case is at "Requires decision".

## 2. Evidence and gaps

- **Provisional credit already given:** established by both `dispute-status.json` (credit £900.00, type provisional, PC-023) and `account-entries.csv` (PC-023 +900.00 `provisional_booked`). The customer herself acknowledges it in E03.
- **No merchant refund posted:** `account-entries.csv` shows MR-023 at £0.00 as of 09:20, ten minutes after the merchant email. This is the latest ledger snapshot supplied.
- **Merchant promise only:** E02 is an email from the merchant to the customer. It contains no processing reference and no evidence of a submitted refund. Under the supplied procedure it is explicitly not a posting event.
- **Labelling difference:** the merchant email refers to `SYN-ORDER-023`; the ledger reference is `ORDER-023`. The plan treats these as the same £900 purchase and nothing in the file contradicts that, but the file does not reconcile the two labels.
- **Cannot be established from the file:** whether or when the merchant refund will actually post; the merchant's processing reference; the disputes team's eventual determination on DB-023. The three-working-day timing is the merchant's expectation only.
- **Authentication:** E01 records authentication passed and E03 is logged as an authenticated chat; identity authority is treated as established. E05 is logged as "Customer chat" without the "Authenticated" label, but it continues the same contact; the plan does not rely on E05 for anything other than the content of the request, and the decision is a refusal, so this does not change the outcome.

## 3. Why this plan

**s1 — decline the second credit and the closure request.**
Explanation: a second £900 would give the customer the same £900 twice for one purchase — once as PC-023, once as a new credit — with no posted merchant refund to reconcile against. Closing DB-023 "as won" is a disputes-team determination, not something the desk does on customer instruction. Evidence: `account-entries.csv` (PC-023 booked, MR-023 £0.00), `dispute-status.json` (open, provisional, procedure text), `history.md` E02/E05. Criterion: a refund promise is not a booked credit; adjustments to a provisional credit follow reconciliation of a *posted* merchant refund. Source: the supplied bank procedure in `attachments/dispute-status.json` — this is a supplied bank policy, not a skill handling rule or a legal obligation. The customer's suggestion that any later merchant payment "can be sorted afterwards" is the reverse of the supplied procedure's ordering (reconcile first, adjust after).

**s2 — pass the merchant email to the disputes team.**
Explanation: the merchant's agreement to refund is material to reconciliation of DB-023 and belongs with the team that owns that step; the desk should neither ignore it nor pre-empt the outcome. The note must say plainly that the desk has authorised no adjustment and has declined the additional £900, so the team's file reflects the desk's actual position. Evidence: `history.md` E02, `dispute-status.json`, `account-entries.csv`. Criterion: the disputes team reconciles any posted merchant refund against the provisional credit before authorising an adjustment (supplied procedure). Source: skill handling rule (payments skill) for routing the information; the underlying criterion is the supplied bank procedure.

**s3 — reply to the customer.**
Explanation: the customer needs the recorded ledger and dispute status, the reason the second credit is declined, what is being passed on, and what remains pending — without promising the merchant refund, its timing, or the dispute outcome. Evidence: the same three sources. Criterion: state only the stage the supplied record proves; a refund promise is not proof of a posted credit; no arrival time is promised absent an applicable commitment. Source: skill handling rule (payments skill).

**Order and dependencies:** s1 is the decision of record and has no prerequisites. s2 and s3 both require s1, because both communicate that decision (the team note states the desk's refusal; the customer message explains it). s2 and s3 are independent of each other.

**Alternatives considered within the plan's scope:** crediting the second £900 now and clawing back later would contradict the supplied procedure and create a duplicate credit; closing as won at the desk would usurp the disputes team's determination. Neither is supported by the file. The plan does not escalate (no `escalate_if`, no safety flags): identity is established and there is no fraud or security indicator — the request is simply premature under the procedure.

## 4. Execution boundaries

- **s1** is a desk decision with no ledger operation: PC-023 remains `provisional_booked`, DB-023 remains open.
- **s2** sends a note; it does not authorise anything. The disputes team's recording, monitoring and reconciliation are their actions, and their acknowledgement is outstanding.
- **s3** is a chat reply using the plan's wording. It must not state any credit or closure outcome.
- The plan stops here. It does not decide what happens once the merchant refund posts, nor the final determination on DB-023; both are for the disputes team after reconciliation. If any step cannot be executed as written, that needs a fresh decision rather than an improvised alternative.

## 5. Expected result and limits

If executed, the steps would: (a) record a reasoned refusal of the duplicate credit and closure request; (b) place the merchant's refund promise and the current MR-023/PC-023 position on the DB-023 file for monitoring and reconciliation; (c) give the customer an accurate account of the recorded status and what to send next (the processing reference).

What remains unconfirmed: whether and when Cresswheel Furnishings' refund posts to SYN-ACCT-B023; the merchant's processing reference; the disputes team's final outcome on DB-023; and the disputes team's acknowledgement of the s2 note.

Message constraints carried from the plan — the customer reply must state: PC-023 (£900) is already on the account while DB-023 is open; no merchant refund has posted as of 11 November 09:20 (MR-023 £0.00) and the merchant email is a promise, not a posting; a second £900 is refused because it would duplicate PC-023 and the disputes team reconciles posted refunds before any adjustment; the desk cannot close DB-023 as won, the disputes team determines the outcome; the merchant email is being passed to the disputes team (pending acknowledgement) and the customer may send the processing reference when received. It must not: promise or imply a second £900 now or later; say the dispute is closed, won or resolved; claim the merchant refund has been received or will arrive within three working days; describe the provisional credit as final or permanent; or claim the disputes team has already recorded or acted on the merchant email.
