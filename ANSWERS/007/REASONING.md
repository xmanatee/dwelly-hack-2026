# Decision memo: case 007, sharing out a returned tenancy deposit

## 1. What happened
All events are dated 2026-09-22. The full input is in the saved `context.md`.

**Bank records:**
- **event-001** (internal account view): Miya Yagisawa's personal current account had a balance of £412.30 before 22 Sep. At 10:05 a credit of £1,260.00 arrived from "OAKFIELD PM CLIENT A/C", reference "DEP RETURN 7 ISFIELD RD".
- The same record shows CoP results for three new payees:
  - Salvatore Russell: match
  - Jack Elson: match
  - Emerald Creagh: no match, name held as "E CREAGH-DOYLE"
- `attachments/cop_results.json` gives the same results. It adds reason code ANNM and each payee's sort code and account number.

**What the customer told us:**
- **event-002** (in-app chat, from her authenticated personal banking): she was lead tenant. The deposit was £1,800, or £450 each, and the landlord kept £540. She asked for Salvatore £247.50, Jack £375.00 and Emerald £337.50, keeping £337.50 herself, and asked for them to go "today". She attached `deposit_split.csv`.
- **event-003:** the agent said they would check the amounts. Nothing has been sent.
- **event-004:** she said "everyone agreed the deductions in writing. Just needs sending."

**Third-party document:** `attachments/agency_deposit_statement.pdf` (Oakfield Property Management, ref DEP/7ISF/2026, dated 22 September 2026). It shows:
- deductions totalling £540.00, agreed in writing by all four tenants on 18 September 2026
- £1,260.00 returned to the lead tenant
- shares of M. Yagisawa £337.50, S. Russell £247.50, J. Elson £337.50 and E. Creagh £337.50

## 2. Evidence and gaps
- **Salvatore:** £247.50 is the same in event-002, the CSV and the agency statement, and his CoP matched. There is no conflict.
- **Jack:**
  - Miya asked for £375.00 (event-002), and the CSV amount column also says 375.00.
  - But her own CSV note says "450 - 75 - 37.50", which is £337.50, and the agency statement also says £337.50.
  - Her four amounts add up to £1,297.50, which is £37.50 more than the £1,260.00 received (event-001). Using £337.50 for Jack gives exactly £1,260.00.
  - We don't know why she wrote £375.00. The plan treats it as a likely typo and asks her to confirm it.
- **Emerald:** CoP gave no match (ANNM), with the name held as "E CREAGH-DOYLE". We can't tell from the records whether this is the same person under a longer name or a wrong account. Only Miya, by checking with Emerald, can settle it.
- **Deductions:** Miya's statement that the deductions were agreed in writing (event-004) is backed by the agency statement. The plan doesn't question them. The only issue is the arithmetic for Jack.
- **Balance:** only the balance before 22 Sep and the credit are recorded. No current balance should be given as a recorded figure.

**Information still needed:**
1. Miya's confirmation that Jack should get £337.50, not £375.00.
2. Miya's confirmation that SYN-SC-07-1 / SYN-ACCT-07-2 belongs to Emerald, under the name held at her bank. She should check this directly with Emerald, using a contact she already knows.

## 3. Why this plan
Identity and authority are established. Miya is asking from her own authenticated in-app chat about her own account (event-001, event-002, request.md). No safety flags were raised.

- **s1: hold Jack's and Emerald's payments.**
  - Why: Jack's amount disagrees with both the agency figure and Miya's own working. Emerald's account name failed the CoP check. Sending now risks overpaying Jack or paying the wrong account.
  - Evidence: event-002, deposit_split.csv, agency_deposit_statement.pdf, cop_results.json, event-001.
  - Rule applied: identify the exact transaction by amount and parties, and hold any payment whose amount or payee details conflict with the records until the customer resolves it.
  - Source: `skill:payments`. This is a handling rule from the skill, not a supplied bank policy or a legal obligation.
  - The hold covers only these two payments. Nothing else on the account is restricted.
- **s2: ask Miya to confirm Salvatore's £247.50 in the app.**
  - Why: the amount is the same in all three sources and the CoP matched. Nothing justifies holding it, and Miya has authority over her own account.
  - Evidence: event-002, CSV, agency statement, cop_results.json.
  - Rule applied: use the authoritative records directly. A fully consistent payment can go ahead once the account holder confirms it.
  - Source: `skill:payments`.
  - The payment isn't sent until she confirms it.
- **s3: reply to Miya.**
  - Why: two specific facts from her are needed before the held payments can be decided. The reply tells her where each payment stands without saying anything has been sent.
  - Evidence: event-001, event-002, event-004, agency statement, CSV, cop_results.json.
  - Rule applied: state only the payment stage the records support, ask for the specific missing facts, and don't promise arrival times without an applicable commitment.
  - Source: `skill:payments`.

**Order of steps:** the hold (s1) and the confirmation request (s2) come before the reply (s3), because the reply describes them. That's why the exact reply wording is kept as a draft that depends on s1 and s2 being confirmed as done.

## 4. Where the plan stops
- No step depends on another, and none has conditions. Nothing escalates.
- Salvatore's payment goes only after Miya confirms it in the app.
- Jack's and Emerald's payments stay on hold until she replies with the two missing facts. What happens after that needs a fresh decision. This memo doesn't set out what that decision should be.
- Her request to send "today" (event-002) is not promised.

## 5. Expected result and limits
**What the steps could achieve:** one consistent payment ready for Miya to confirm, two held payments, and a clear request for the two missing facts.

**What remains unconfirmed:**
- whether Miya will confirm Salvatore's payment
- what Jack's correct amount is
- whether Emerald's account details are right
- when any payment would arrive

**The message must state:**
- No payments have been sent yet. Salvatore's £247.50 is waiting for Miya's in-app confirmation.
- The agency statement and Miya's own working both give Jack's share as £337.50, not £375.00. Her four amounts add up to £1,297.50, but £1,260.00 was received.
- Emerald's CoP check returned no match, with the name held as "E CREAGH-DOYLE". Miya should check the details with Emerald directly before that payment is sent.
- Jack's and Emerald's payments are on hold until Miya replies.

**The message must not:**
- say any payment has been sent, received or confirmed
- send £375.00 to Jack, or anything to Emerald, before Miya confirms
- suggest Emerald's account is fraudulent or definitely wrong
- promise arrival today or at any set time
- give a current balance as a recorded figure
- question the agreed deductions

**One point for the operator:** the plan's exact reply describes the payment as being with Miya in the app for her to approve. That refers to the confirmation request, not to money leaving the account, and the next sentence says it won't go until she approves it. But the reply doesn't use the exact words "No payments have been sent yet." When the draft is used, check that the reply makes that point clearly.
