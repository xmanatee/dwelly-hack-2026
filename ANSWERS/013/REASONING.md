# Decision memo: case 013, rent Direct Debit and unpaid notice

The full input is saved in `context.md`.

## 1. What happened

**From the bank's own records (authenticated):**
- **event-001** (internal account view, 23 Sep 2026) covers Rina Patel's Direct Debit to H&V COLLECT / NORTHGATE LETTINGS, £750 a month:
  - **18 Sep:** the collection was returned unpaid ("refer to payer"). The available balance was £710.40.
  - **19 Sep:** an automated unpaid letter was sent.
  - **21 Sep:** Northgate collected again and it was paid. Her salary had come in on 20 Sep.
  - H&V charges no unpaid-item fee, and nothing else is due before 18 Oct.
- **`attachments/statement_extract.csv`** shows the same thing:
  - 18 Sep: "DD RETURNED … NL-9LIME-0442 (refer to payer)", balance 710.40.
  - 20 Sep: salary of £2,145.00 from BRIGHTON & CO LLP, balance 2,855.40.
  - 21 Sep: "DD … NL-9LIME-0442 (re-presentation)" for -750.00, balance 2,105.40.
- **`attachments/unpaid_dd_letter_2026-09-19.pdf`** is dated 19 September 2026. It says the £750 Direct Debit presented on 18 September couldn't be paid and that no fee was charged. It adds that the organisation "may try to collect the payment again, or contact you about it", and points her to the organisation for questions about what she owes.

**From the customer and third parties (not authenticated):**
- **event-002 / request:** Ms Patel says she got the letter, can see £750 leave on the 21st, and has had a text from the agency asking for a manual payment. She doesn't want to be in arrears or to pay twice.
- **`attachments/agency_text_screenshot.png.ocr.txt`:** a machine reading of her screenshot. It shows a text from "Northgate Lettings" sent Tue 22 Sep at 16:20. It says the September Direct Debit "FAILED" and asks for £750 "today to our client account", reference NL-9LIME-0442. The original `agency_text_screenshot.png` couldn't be read, so we only have the OCR text.
- **event-003:** the agent told her, "Let me check both dates on the mandate."

## 2. Evidence and gaps

**What is established:**
- The 18 Sep attempt failed and the 21 Sep collection was paid. Both event-001 and the statement show this.
- The 19 Sep letter is about the 18 Sep attempt. The letter and event-001 agree.
- No fee was charged and nothing more is due before 18 Oct (event-001; the letter also confirms no fee).

**What can't be established:**
- **Northgate's ledger.** We can't tell whether Northgate has recorded the 21 Sep payment or whether they show her in arrears. The bank can't see their system.
- **Who sent the text.** We only have an OCR transcription. The reference in the text matches the one on the statement, but that doesn't prove who sent it either way.
- **Timing.** The text was sent on 22 Sep, the day after the payment. A delay in Northgate's system would explain it, but that's only a possible reason, not a confirmed one.

**The agent's earlier promise.** event-003 said the agent would check the mandate. That check isn't needed, because event-001 already gives both dates.

## 3. Why this plan

**Step s1: reply to the customer (the only action).**
- **Why:** event-001 and the statement already show the 18 Sep return, the 19 Sep letter and the paid 21 Sep collection. That answers her question without another mandate check. The evidence doesn't show Northgate's ledger or who sent the text, so the reply sends her to Northgate through contact details she already trusts. It doesn't tell her she's paid up, and it doesn't call the text fake.
- **Evidence:** event-001, event-002, event-003, `statement_extract.csv`, `unpaid_dd_letter_2026-09-19.pdf`, `agency_text_screenshot.png.ocr.txt`.
- **Rule applied:** use the mandate and collection records directly, and keep a returned collection separate from a later paid one. Bank records don't show whether the merchant has recorded a payment, so don't claim it has.
- **Source:** the skill handling rule `skill:scheduled-payments`. This is a handling rule, not a bank policy or a legal obligation. No bank policy document or legal rule was supplied.

**Why this order and nothing else:**
- Her identity is established (`identity_authority: established`) and there are no safety flags.
- The reply only passes on information. It doesn't need a payment reversal, a Direct Debit Guarantee claim, a handoff or another lookup.
- Mentioning the £1,500 total speaks to her worry about paying twice. Telling her to use trusted contact details protects her if the text isn't genuine, without accusing anyone.

## 4. What the plan covers and where it stops

- The only pending step is **s1**: sending the drafted reply in the current in-app chat. It has no conditions and doesn't depend on anything else.
- The plan stops at the reply. There are no escalation triggers or follow-up steps. Whether she is in arrears and whether the text is genuine are left for her to settle with Northgate directly.
- If anything new comes up, it needs a fresh decision rather than extra steps added here.

## 5. Expected result and limits

**What the reply can do:**
- Explain why she got both the letter and the 21 Sep debit.
- Confirm from bank records that September's £750 left her account once, with no fee and nothing more due before 18 Oct.
- Warn her that paying manually would mean paying twice.

**What stays unconfirmed:** whether Northgate shows her in arrears, and whether the text came from Northgate.

**The reply must say:**
- The 18 Sep collection was returned unpaid because only £710.40 was available, and the 19 Sep letter is about that attempt.
- The 21 Sep collection was paid, so bank records show September's rent paid once.
- No fee was charged, and no further collection is scheduled before 18 Oct.
- A manual payment would mean £1,500 paid to Northgate for September.
- The bank can't confirm Northgate's records or whether they show her in arrears. She should contact Northgate using details she already has and quote the 21 Sep payment, reference NL-9LIME-0442.
- The 22 Sep timing may mean Northgate's system hasn't caught up. This is a possible reason only.

**The reply must not:**
- Say Northgate has received, matched or recorded the payment, or that she definitely isn't in arrears.
- Call the text a scam, or say it's definitely genuine.
- Tell her to make the manual payment, or promise a refund if she pays twice.
- Say the 21 Sep payment can be reversed, or that a Direct Debit Guarantee claim applies.
- Say the bank will re-check the mandate or come back to her later.
- Ask for PINs, passwords or one-time codes.

The drafted message meets all of these points.
