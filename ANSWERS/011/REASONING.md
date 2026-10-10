# REASONING — Case 011: Refund of duplicate £1,096.00 credit

Full input is in the saved `context.md`. All actions below are proposed; none has been executed.

## 1. Situation and history

**Customer:** Paul Devlin t/a Devlin Plumbing, sole-trader business account SYN-SC-11-1 / SYN-ACCT-11-1 at Harrow & Vale Bank plc. Contact is via the bank's business banking chat on 2026-09-23 (individual event times not recorded; events follow conversation order).

**Authenticated bank records (event-001, `attachments/inbound_payments.json`):**
- 21 Sep 2026 09:40 BST — Faster Payment credit +£1,096.00, payer name text "A KOWALCZYK", Meridian Bank SYN-SC-11-2 / SYN-ACCT-11-2, reference "INV 2211 BOILER", end-to-end ID MER26092109401201.
- 22 Sep 2026 14:20 BST — Faster Payment credit +£1,096.00, same payer name text, same payer sort code/account, same reference, end-to-end ID MER26092214204811.
- Confirmation of Payee (`attachments/cop_result_refund_details.json`) on SYN-SC-11-2 / SYN-ACCT-11-2, name supplied "M Kowalczyk", account type personal: `matched: true`, name at bank "M KOWALCZYK", checked 2026-09-23T10:05:33Z.

**Customer's report (event-002, event-004, `request.md`):** Paul states his customer paid invoice 2211 twice and has texted him asking for one payment to be returned to "her husband's account" SYN-ACCT-11-2 / SYN-SC-11-2, M Kowalczyk, "that's what I paid from". When the agent queried the A/M name difference (event-003), Paul said Anna is the client, Marek is her husband, the money is joint, the account is Marek's and she uses it; he wants to refund but not to the wrong place.

**Forwarded third-party message (`attachments/client_text_message.txt`):** text dated Tue 22 Sep 19:02 from a number saved as "Anna K - boiler job", attributing the duplicate to an app glitch and asking for one payment back to the same details. This is a forwarded message supplied by Paul, not an instruction verified by the bank.

## 2. Evidence and gaps

**Established from authenticated records:**
- Two credits of identical amount, reference and source account one day apart, with distinct end-to-end IDs — consistent with a duplicate payment (event-001, `inbound_payments.json`).
- The refund destination (SYN-SC-11-2 / SYN-ACCT-11-2) is character-for-character the originating sort code and account number of both credits (`inbound_payments.json` vs event-002 and `client_text_message.txt`).
- CoP matches "M KOWALCZYK" on that account (`cop_result_refund_details.json`).

**Observed discrepancy:** the inbound payer name text is "A KOWALCZYK" while the account name at the receiving bank is "M KOWALCZYK" (event-003). Paul's explanation (event-004) is a customer assertion the bank cannot verify. It is not contradicted by the records, but it is also not corroborated by them: the payer-name text in a Faster Payment message is not a verified account-holder name, and this bank has no view of the Meridian account's holders or mandate.

**Gaps (from the plan's `missing` list):**
1. Whether Meridian Bank has already lodged a recall or return request for either end-to-end ID. The supplied snapshot records none, but this is an absence of record in the snapshot, not a negative finding — the payer said the app "glitched" and may also have contacted her own bank.
2. Paul's secure confirmation of the outbound £1,096.00 payment — not yet given; the chat exchange is a request, not an authorised payment instruction.
3. Independent evidence of who holds the Meridian account or of the Anna/Marek relationship — not obtainable by this bank, and per the plan not required, because the payment goes back to the account the funds came from rather than to a new destination.

**Identity:** the plan records identity authority as established (account holder in the bank's business banking chat about his own account). No separate verification record is supplied; this is noted as a limit rather than a contradiction.

## 3. Why this plan

**Core judgement (plan summary):** the risk Paul raised — "sending it to the wrong place" — is addressed not by resolving the name difference but by the fact that the destination is the exact originating account, confirmed by CoP. The A/M difference is therefore unverified but immaterial to a return-to-source. Had the client asked for the refund to go to any *different* account, the same evidence would not support proceeding; that alternative is not the case here and is not part of the decision.

**s1 — check recall/return records first.**
- *Explanation:* if Meridian has already lodged a recall, a customer-initiated refund would return the same £1,096.00 twice.
- *Evidence:* `inbound_payments.json` (the two end-to-end IDs), `client_text_message.txt` (the "app glitched" account that could prompt a recall at the payer's bank), event-001 (snapshot shows no recall recorded).
- *Criterion:* a named journal lookup is justified only for a material gap; a recall/return request is distinct from a completed return and must not be duplicated.
- *Source:* skill:payments handling rule (not a supplied bank policy or legal obligation).

**s2 — set up the payment for Paul's secure confirmation (after s1).**
- *Explanation:* Paul is the account holder instructing a payment from his own account; the destination is the originating account and CoP matches. The payment is state-changing and requires his secure authorisation; it is also gated on s1 showing no existing Meridian recall for the credit being returned (MER26092214204811, the second credit).
- *Evidence:* event-002 (request), event-004 (confirmation of intent), `inbound_payments.json`, `cop_result_refund_details.json`.
- *Criterion:* identify the exact transaction by reference, amount, date and parties; a customer-authorised outbound payment requires the customer's secure confirmation before release.
- *Source:* skill:payments handling rule.

**s3 — reply to the customer (after s1 and s2).**
- *Explanation:* answers the concern with the evidenced basis (same source account, CoP match), labels the unverified assertions as such, states that nothing has been sent and that release depends on the recall check and his confirmation, and avoids any arrival-time promise.
- *Evidence:* event-003, event-004, `cop_result_refund_details.json`, `inbound_payments.json`.
- *Criterion:* state only the stage the supplied record proves; do not promise arrival times absent an applicable commitment.
- *Source:* skill:payments handling rule.

**Ordering:** s1 precedes s2 because the recall check determines whether the refund should be released at all; s2 precedes s3 so the message accurately describes a payment that is set up and awaiting confirmation rather than one that is still hypothetical. The message text in s3 is nonetheless written so that it remains truthful if read before s2 is complete ("Nothing has been sent yet… I'll then send you a payment… to confirm").

**Safety flags:** none raised in the plan. The refund is to the originating account, which removes the main redirection risk; CoP is a match, not a near-match or mismatch.

## 4. Execution boundaries

- **s1** has no dependencies and can proceed immediately. Its result must be recorded on case 011 before anything else is released.
- **s2** requires s1. Release of the payment is additionally conditional on (a) s1 showing no existing Meridian recall for MER26092214204811 and (b) Paul's secure confirmation in the business banking channel. If s1 shows a recall or return request already lodged, the plan does not authorise release; that would require a fresh decision, not an alternative devised here.
- **s3** requires s1 and s2 and is the only customer-facing communication in the plan.
- The plan stops at Paul's confirmation. It does not pre-decide what happens if he declines, if CoP changes, or if Meridian contacts the bank later. No escalation conditions are set (`escalate_if` is empty).

## 5. Expected result and limits

**What the steps could achieve:** confirmation that no double return is in train; a £1,096.00 Faster Payment to SYN-SC-11-2 / SYN-ACCT-11-2 with reference "REFUND INV 2211 DUPLICATE" queued for Paul's secure authorisation; and a clear explanation to Paul of why the refund can proceed despite the name difference and what the bank cannot verify.

**What remains unconfirmed:** whether a Meridian recall exists (until s1 is run); whether Paul will confirm; who holds the Meridian account and whether Anna is authorised on it (not verifiable by this bank); arrival timing (no commitment given).

**Constraints preserved in the message (`must_state`):** same source account → return to source; CoP match to "M KOWALCZYK"; inbound payer name "A KOWALCZYK" and the bank's inability to verify the holder/relationship, with the originating-account basis made explicit; nothing sent yet and release only on secure confirmation; recall check in progress and no arrival-time promise; suggested reference and advice to retain the text and end-to-end IDs.

**Constraints observed (`must_not`):** the message does not say the account is joint, Marek's, or that Anna is authorised; does not say the refund has been sent, credited or will arrive by a time; does not claim the name difference is verified or resolved; discloses nothing about the Meridian account beyond the CoP match already shown; does not treat the forwarded text as a verified payer instruction; does not request a PIN, password or one-time code; and does not state that no recall exists — only that the bank is checking.

**Note on plan sufficiency:** the plan is adequate for the facts supplied. The one point an operator should hold in mind is that the snapshot's silence on recalls is not evidence of their absence, which is exactly why s1 is placed first and gates s2.
