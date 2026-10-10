# Why case 028 (INT-028) is handled this way

The full input is saved in `context.md`. The sources cited here are `history.md` (events E01–E05), `request.md`, `attachments/execution-advice.pdf` and `attachments/recipient-advice.pdf`.

## 1. What happened

**From the bank's own authenticated records:**
- **E01, 2026-11-18 09:00:** Perrin Wessel passed the identity check and gave the instruction in the authenticated portal. The terms were:
  - £1,000 principal and a separate £5 sending fee.
  - Shared charge option.
  - An estimate of EUR1,160 at an indicative rate of 1.1600 EUR/GBP, marked "non-binding until execution".
  - Possible intermediary or receiving-bank charges were disclosed, and the customer confirmed.
- **E02, 09:10:** The international payments team supplied `execution-advice.pdf` (INT-028). It shows:
  - executed at 09:08 at 1.1500 EUR per GBP
  - GBP 1,000.00 converted, EUR 1,150.00 sent
  - GBP 5.00 fee, GBP 1,005.00 total debit
  - charge option SHA
  - destination SYN-ACCT-REC028

**From outside the bank, passed on by the customer:**
- **E03, 10:00:** The recipient, Osa Melwick, emailed Perrin Wessel the advice from her bank, and he forwarded it with its origin shown. `recipient-advice.pdf` was issued by Synthetic Overseas Recipient Bank. It shows:
  - received at 09:50
  - gross EUR 1,150.00
  - "Intermediary deduction reported: EUR 15.00"
  - net credit EUR 1,135.00

**What the customer is asking:**
- **E04, 10:10 (authenticated chat):** "The recipient got EUR1,135… I think EUR25 went missing."
- **E05, 10:15:** He asks for EUR25 compensation today and wants us to say the recipient should have received the estimate.
- `request.md` confirms that no desk response has been recorded yet.

## 2. What the evidence shows, and what it doesn't

**The EUR25 is fully explained:**
- EUR10: 1,000 × 1.1600 = 1,160, minus 1,000 × 1.1500 = 1,150 (E01 against `execution-advice.pdf`).
- EUR15: 1,150 − 15 = 1,135 (`recipient-advice.pdf`).
- The gross amount matches on both sides: EUR 1,150.00 sent and EUR 1,150.00 received. Nothing in the records suggests money was lost.

**Gaps:**
- **The bank cannot confirm the EUR15 itself.** It has no record of which intermediary was involved or of the deduction. The figure comes only from the recipient bank's advice, which reached us through the customer. That is why the reply describes the EUR15 as something the advice "reports" and doesn't claim the bank checked it.
- **There is no complaint reference or acknowledgement yet.**
- **Minor point:** E05 is labelled "Customer chat", while E04 is labelled "Authenticated customer chat". The plan treats identity and authority as established on the strength of E01 and E04. This does not change the decision.
- **What the records can't tell us:** who the intermediary was, why it charged, or whether the complaints team will award anything.

## 3. Why this plan

**s1: send the complaint to the complaints team**
- **Why:** The customer is asking for redress (EUR25 compensation). That makes it a complaint to register on its own track, even though the records explain the difference.
- **Evidence:** `history.md`, `request.md` and both advices.
- **Rule applied:** keep the factual query and the complaint as separate pieces of work. The complaint action must be concrete, not conditional, and must not promise redress.
- **Source:** the skill handling rule `skill:complaints-rights`. No bank complaints policy or legal clause was supplied, so none is cited. The plan also flags `complaint_rights`.

**s2: reply to the customer**
- **Why:** The bank's execution advice and the forwarded recipient advice together explain the full EUR25, so the desk can answer the factual question now. The reply states only what the records show, and it reports the complaint as pending until it is acknowledged.
- **Evidence:** `history.md` and both advices.
- **Rule applied:** use the authoritative status directly and state only what each record proves. Don't promise outcomes, and don't report an operation as done before it is acknowledged.
- **Source:** the skill handling rule `skill:payments`.

**Why s1 comes first:** s2 depends on s1 because the reply mentions the complaint. Sending the complaint request first means the reply can describe its status accurately, either as requested and pending or as confirmed.

**Why we refuse the customer's two requests:**
- **"The recipient should have received EUR1,160":** E01 records that this figure was a non-binding estimate, so saying the recipient should have received it would contradict the records.
- **Paying EUR25 today:** promising payment would get ahead of the complaints team's review.

## 4. Limits on execution
- **Nothing has been executed.**
- **s1:** the complaints team's acknowledgement and reference are still awaited.
- **s2:** depends on s1. If no acknowledgement has arrived when the reply goes out, it must say the registration has been requested and confirmation is pending. The plan's own wording ("I've passed your compensation request…") is kept as a separate draft, to be used only once s1 has been confirmed.
- **What the plan doesn't cover:** it has no escalation conditions and no further steps. It stops at sending the complaint and giving the explanation, and the complaints team's review decides the outcome. If either step is blocked, someone needs to make a fresh decision.

## 5. What this can achieve, and what it can't

**If both steps go ahead:**
- The customer gets a clear EUR10 + EUR15 explanation.
- His compensation request reaches the complaints team for review.

**Still unconfirmed:**
- the complaint reference and any deadline
- the result of the review
- independent confirmation of the EUR15

**The customer message must state:**
- EUR1,160 was an estimate at an indicative rate of 1.1600, non-binding until execution.
- The payment was executed at 1.1500, so EUR1,150 was sent gross. That accounts for EUR10.
- The recipient bank's advice reports a EUR15 intermediary deduction, leaving EUR1,135 credited. That accounts for the other EUR15.
- Possible intermediary or receiving-bank charges under the Shared option were disclosed before the customer confirmed.
- The compensation request is going to the complaints team for review. Registration and the reference are pending, and no outcome is promised.

**The customer message must not:**
- say the recipient should have received EUR1,160
- promise or imply EUR25 compensation, a refund or same-day payment
- claim anyone made an error or that money was lost
- name an intermediary or explain why it charged, beyond what the recipient advice reports
- say the bank independently verified the EUR15
- quote a complaint reference or response deadline that hasn't been recorded
