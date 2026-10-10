# REASONING — Case 013: Rent collection and an unpaid notice

Full input is preserved in `context.md`. Nothing has been executed; the single step below is pending.

## 1. Situation and history

- **event-001 (2026-09-23, internal account view, Harrow & Vale Bank plc):** authenticated bank record for Rina Patel's personal current account. Direct Debit H&V COLLECT / NORTHGATE LETTINGS, £750 monthly. Shows: 18 Sep collection presented and returned unpaid "refer to payer" (available balance £710.40); 19 Sep automated letter issued; 21 Sep collection re-presented by the originator and paid (salary credited 20 Sep). No unpaid-item fee charged; no further collection scheduled before 18 Oct.
- **attachments/statement_extract.csv:** bank statement lines consistent with event-001 — 18 Sep DD RETURNED (balance £710.40); 20 Sep salary credit £2,145.00 (balance £2,855.40); 21 Sep DD −£750.00 marked "(re-presentation)", ref NL-9LIME-0442 (balance £2,105.40).
- **attachments/unpaid_dd_letter_2026-09-19.pdf:** the bank's automated letter for the 18 Sep presentation; confirms no fee and states the organisation may try to collect again.
- **event-002 (2026-09-23, in-app chat, customer's report):** Rina received the letter, can see £750 leaving on 21 Sep, and has a text from "the agency" saying the payment failed and asking for a manual payment today. She wants to avoid arrears and avoid paying twice.
- **attachments/agency_text_screenshot.png.ocr.txt:** OCR of the text, attributed to "Northgate Lettings", dated Tue 22 Sep 16:20, saying the September Direct Debit "FAILED" and requesting a manual £750 payment to their client account, ref NL-9LIME-0442.
- **event-003 (2026-09-23, agent):** "Let me check both dates on the mandate." — the agent's last message, before any answer was given.

Distinction: event-001, the statement extract and the 19 Sep letter are the bank's own records. Event-002 and the text screenshot are the customer's report and a third-party message respectively; the text's origin is not verified by any bank record.

## 2. Evidence and gaps

**Established by bank records**
- The 18 Sep return and its cause (available balance £710.40 < £750), no fee: event-001, statement_extract.csv, unpaid_dd_letter_2026-09-19.pdf.
- The 19 Sep letter relates to the 18 Sep attempt: the letter itself names "Date presented: 18 September 2026".
- The 21 Sep re-presentation was paid and £750 debited, ref NL-9LIME-0442: event-001, statement_extract.csv.
- Mandate active, next collection not before 18 Oct: event-001.

**Not established (the plan's `missing` items)**
- Whether Northgate Lettings has received and reconciled the 21 Sep collection. The bank's records show the debit from Rina's account only; they say nothing about the recipient's credit or the agency's ledger.
- Whether the 22 Sep text genuinely came from Northgate. The reference NL-9LIME-0442 matches the mandate reference on the statement, which is consistent with a genuine but stale system message, but it is not proof of either genuineness or impersonation. The agency's text post-dates the 21 Sep payment, so a plausible explanation is that their system still reflects the 18 Sep failure — but that is inference, not record.

**Apparent contradiction explained:** the customer sees "failed" (letter + text) and "paid" (statement) for the same rent. These are two separate presentations of one collection: the first (18 Sep) failed, the second (21 Sep) succeeded. There is no contradiction in the bank's records.

## 3. Why this plan

The plan has one step, **s1 — reply_to_customer**, with no dependencies.

- **Explanation (plan rationale):** the internal account view already contains both mandate dates, so the lookup the agent proposed in event-003 is already satisfied by event-001; the question can be answered now. The reply must state only what the bank's record proves (the 21 Sep debit) and must not assert that the agency has reconciled it, and must steer the customer away from paying on the strength of an unverified text.
- **Evidence cited by the plan:** event-001, event-002, statement_extract.csv, unpaid_dd_letter_2026-09-19.pdf, agency_text_screenshot.png.ocr.txt.
- **Decision criterion:** state only the payment stage the supplied record proves (paid on re-presentation, not recipient credit); an active mandate or a letter does not establish the later collection's outcome; a third party's message is not evidence of a booked or missing payment; unexpected payment requests should be verified through a known trusted contact route.
- **Rule source:** `skill:scheduled-payments` — this is the skill's handling rule, not a supplied bank policy document or a legal obligation. No bank policy or statutory text was supplied in the case materials, and none is cited here.

**Why no bank-side action:** the mandate behaved correctly (returned for insufficient funds, then re-presented and paid); no fee was charged; the next collection is not before 18 Oct. Nothing indicates a mandate error, so cancelling or amending the mandate would not be supported by the evidence (`must_not`). The customer has not asked the bank to send any payment (event-002, request.md).

**Why advise against the manual payment now:** paying would create the double-payment risk the customer wants to avoid, and the only basis for the request is a message whose authenticity and currency are unverified. The safe route is confirmation with Northgate via details she already holds (tenancy agreement / official website), not the text's contact details (`must_not`: do not quote the text's contact details as trusted). If Northgate deny sending the text, the plan asks her not to pay and to report back to the bank as a possible impersonation; the plan does not go further than that.

**Alternatives considered within the plan's bounds:** a further internal lookup (as event-003 suggested) adds nothing because event-001 already covers both dates. Treating the text as definitely a scam or definitely genuine is not supported either way, so the message states neither.

## 4. Execution boundaries

- Only **s1** is proposed; it has no `requires` and no condition. It is pending until sent.
- The plan stops after the reply. It does not commit the bank to any action on the agency's side, does not open a fraud/impersonation case (that would only arise if the customer returns with Northgate's denial, which the plan treats as a report-back, not a pre-authorised step), and does not propose any Direct Debit Guarantee or refund route.
- If the customer returns with new information (e.g. Northgate disown the text, or say they have not received the 21 Sep funds), that requires a fresh decision; no branch is pre-decided here.
- `escalate_if` is empty and `safety_flags` is empty; identity authority is established, so the in-app reply can be given.

## 5. Expected result and limits

**What s1 can achieve:** gives the customer a clear, record-based account of the 18/19/21 Sep sequence; reassures her that, from the bank's side, September's rent has been collected and no further collection is due before 18 Oct; prevents a premature duplicate payment; directs her to verify the text through a trusted route. Expected disposition: completed.

**What remains unconfirmed:** whether Northgate has received/reconciled the 21 Sep payment, and whether the 22 Sep text is genuine. Both can only be resolved by the customer's contact with Northgate; the bank cannot confirm them from its own records.

**Constraints preserved in the message:** all `must_state` items are covered (18 Sep return and £710.40 balance, letter linkage, no fee; 21 Sep re-presentation paid ref NL-9LIME-0442 after the 20 Sep salary; bank record proves debit only; do not pay yet and verify via trusted contact, not the text; no bank action, mandate unchanged, next collection not before 18 Oct; report back if Northgate deny the text). `must_not` items are respected: the message does not tell her to pay manually, does not claim the agency has reconciled the payment, does not call the text genuine or a scam, does not promise a refund or Guarantee claim, does not suggest cancelling or amending the mandate, and does not quote the text's contact details as trusted.
