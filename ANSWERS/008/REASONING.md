# Decision memo — case 008, "New rent payment details"

Full input is saved in `context.md`. This memo records the public grounds for the plan of record; nothing has been executed.

## 1. Situation and history

**Authenticated records (bank side)**

- `event-001` (internal account view, 2026-09-23) and `attachments/standing_order_on_file.json`: Nicole Hart, personal current account, has an active £1,150 standing order on the 25th to "Miss D L Hanlon", Meridian Bank SYN-SC-08-1 / SYN-ACCT-08-2, reference "RENT 26 BROAD LANE", created 2025-03-10, CoP **matched** at creation, last paid 2026-08-25, zero failures.
- `attachments/cop_result_new_details.json`: CoP on the new details (SYN-SC-08-2 / SYN-ACCT-08-1, name supplied "Miss D L Hanlon", type personal) returned `matched: false`, reason code **ANNM** ("Account name does not match"), name at bank **DLH PROPERTY SERVICES LTD**, account type **business**, checked 2026-09-23T10:12:02Z.
- Identity authority is recorded as established (authenticated in-app chat).

**Customer's report and supplied material**

- `event-002` (in-app chat, contact start 11:10 UK): the customer asks for the standing order to be redirected to SYN-SC-08-2 / SYN-ACCT-08-1, "Miss D L Hanlon", "today" because the payment runs on the 25th, pasting an email received that morning.
- `attachments/landlord_email_as_forwarded.eml`: From "Debbie Hanlon" `<dl.hanlon.property@sender.example>`, Reply-To `dlh.accounts.desk@reply.example`, dated Wed 23 Sep 2026 07:48:19 +0100, webmail. Body says she has switched banks, the old account "closes today" and anything sent there "will bounce".
- `attachments/customer_previous_landlord_emails.txt` (customer's own note): three earlier landlord emails (2025-03-04, 2025-12-18, 2026-06-02) all from `debbie.hanlon@btinternet.example` — a different address from today's sender and from the Reply-To.
- `event-003`: the agent tells the customer the CoP result must be discussed before any change.
- `event-004`: the customer says the landlord "did mention going limited at some point", believes it is her, and asks for the mismatch to be overridden because "she's been my landlord for years".

No payment has been recorded as sent to the new details and the payee has not been changed (`event-003`, `attachments/standing_order_on_file.json`).

## 2. Evidence and gaps

**What is established**

- The CoP mismatch is a bank-obtained record, not a customer claim: the receiving account is a business account named DLH PROPERTY SERVICES LTD, while the customer was told to pay "Miss D L Hanlon" as a personal payee (`cop_result_new_details.json`).
- The existing standing order was CoP-matched at creation and has paid without failure for 18 months (`standing_order_on_file.json`).
- The email's sender and Reply-To both differ from the address on every prior landlord email in the customer's note (`landlord_email_as_forwarded.eml` vs `customer_previous_landlord_emails.txt`), and the message imposes same-day pressure.

**What is asserted but not verified**

- That the landlord has "gone limited" and is now DLH PROPERTY SERVICES LTD (`event-004`) — the customer's recollection, not confirmed with the landlord.
- That the old account "closes today" and payments there "will bounce" — stated only in the suspect email.

**Gaps (per the plan's `missing` list)**

1. Independent confirmation from the landlord via a contact route the customer already trusted before today.
2. Whether SYN-SC-08-1 / SYN-ACCT-08-2 is actually closed.
3. The fraud/security team's assessment.

**Contradictions.** The payee name the customer was given ("Miss D L Hanlon", personal) contradicts the name and account type held at the receiving bank (business). The email's "going limited" explanation offered by the customer could reconcile this, but the email itself does not say so — it presents the account as "my new account" in a personal voice. The sender/Reply-To mismatch with the historical address cannot be explained from the material supplied. None of this proves the email is fraudulent; it means the bank cannot tell from the email alone, and the plan treats it as a suspected scam pending verification.

## 3. Why this plan

**s1 — Decline override, hold the payee change** (`skill:fraud-takeover` handling rule: suspected scam → hold the specific risky action; do not facilitate on a customer assertion alone). Grounds: `cop_result_new_details.json`, `landlord_email_as_forwarded.eml`, `customer_previous_landlord_emails.txt`, `event-004`. The CoP result directly contradicts the supplied payee name, and the email carries recognised redirection-scam markers (new sender, different Reply-To, urgency, "old account closes today"). The customer's belief is sincere but unverified. The hold is narrow: only the payee change is held; the existing, long-matched standing order is left untouched and no other banking is affected.

**s2 — Urgent fraud/security referral** (`skill:fraud-takeover` handling rule: impersonation/redirection warning signs require an urgent fraud/security handoff alongside the hold). Grounds: `event-001`, the CoP result, the email headers, the prior-email note. The warning signs are concrete, not speculative, and a loss could occur on the 25th if the change were made, so review is warranted even though no money has moved. The referral packet is limited to facts already in the record; it asks the team to assess and advise on any further protection for the 25th collection, without the plan predicting what they will decide.

**s3 — Ask the customer to verify via a trusted route** (`skill:fraud-takeover` handling rule: verify through a known trusted contact, never through details supplied by the suspected source). Grounds: `event-004`, the email, the prior-email note. The only thing that can safely resolve the mismatch is confirmation from the genuine landlord through a route that pre-dates today's email. Replying to the email, or using its Reply-To, would let the suspect message verify itself.

**s4 — Customer reply** (`general:planner`: reply with recorded status, what is on hold, and what has not been confirmed). Grounds: `event-003`, `event-004`, the CoP result, the standing order on file. The customer needs the CoP finding, the specific reasons, reassurance that nothing has moved and her rent payment is untouched, a safe verification path, and an honest statement that the outcome depends on the fraud review and the landlord's confirmation. The reply deliberately does not call the email fraudulent, does not say the old account is closed, and does not predict whether the 25th payment will succeed.

**Order.** s1 and s2 have no dependencies and should proceed first; s4 depends on both so the customer is told about a hold and a referral that have actually been actioned. s3 is the request embedded in the reply.

**Alternatives considered within the plan's scope.** Overriding CoP on the customer's assertion (`event-004`) was rejected because the mismatch is to a different legal entity and account type and the supporting explanation is unverified. Changing the payee conditionally "to be safe before the 25th" would move £1,150 to an unverified business account — the exact harm the hold prevents. These are rule sources from the skill, not a supplied bank policy document or a stated legal obligation; no bank policy text or statute was supplied in this case.

## 4. Execution boundaries

- **s1** and **s2** are independent and can be actioned together. **s4** requires acknowledgement that s1 and s2 have been executed; the draft wording that refers to the hold as already in place is held in `future_messages` and labelled NOT SENT until then.
- The plan stops after s4. It does **not** decide what happens if the landlord confirms or denies the details, or what the fraud team recommends; those require a fresh decision with the new information. The plan's `escalate_if` list is empty.
- No action in this plan alters the existing standing order, blocks the account, sends any payment, or contacts the landlord on the customer's behalf.

## 5. Expected result and limits

**What the proposed steps could achieve:** prevent an unverified redirection of £1,150; get a fraud/security assessment before the 25th; give the customer a safe way to resolve the question herself; keep her existing rent payment untouched.

**What remains unconfirmed:** whether the landlord genuinely trades as DLH PROPERTY SERVICES LTD and holds the new account; whether the old payee account is closed and what will happen to the 25th collection; the fraud team's conclusions and any further protection they recommend.

**Constraints carried into the customer message (`must_state`):** CoP result and hold; the specific warning signs; nothing sent and existing order unchanged for the 25th; verify via a pre-existing trusted route only; fraud review is being requested and next steps depend on it and the landlord's answer; the request can be reconsidered on trusted confirmation.

**Constraints observed (`must_not`):** no override or payee change on assertion alone; no statement that the email is fraudulent or that the landlord is/is not DLH PROPERTY SERVICES LTD; no claim the old account is closed or the 25th payment will bounce/succeed; no reimbursement promise or review timescale; no verification via the new email or its Reply-To; no PINs, passwords or one-time codes; no claim that the referral or hold is already executed.

**Residual uncertainty:** the "going limited" explanation is plausible and the plan does not dismiss it; if confirmed through a trusted route it would materially change the picture, but that is for a subsequent decision.
