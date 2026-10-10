# Decision memo: case 019, recall request for a payment made twice

The full input is in the saved `context.md`. This memo cites only the event IDs and attachments supplied there.

## 1. Situation and history
- **Bank record (event-001, internal account view as at 2026-09-23):**
  - Linda Ferris has a personal current account. She is a landlord, and Oakfield PM manages her property at 53 Winchester Road.
  - The account view shows one entry: on 12 Aug, a debit of −£651.00 by Faster Payment to CO-CLEAN SERVICES LTD, ref "INV 4471 53 WINCHESTER". It was a new payee and a Confirmation of Payee match at the time.
- **Bank payment confirmation (`attachments/payment_confirmation_2026-08-12.pdf`):**
  - Faster Payment HV26081210144802, 12 Aug 2026 at 10:14, £651.00, status **Completed**.
  - It says the payment was "received by the beneficiary bank". It also says it is not a receipt from the beneficiary.
- **What the customer says (event-001 note, event-002, request.md):**
  - Oakfield PM paid the same invoice 4471 from her rental funds on 15 Aug.
  - Co-Clean agreed on 17 Sep to refund £651 "on the next payment run".
  - She says it has been a week, and asks the bank to recall the payment so she gets the money back faster.
- **Chat so far:**
  - The agent replied that they would look at the payment and explain what a recall would and wouldn't do (event-003).
  - The customer then asked: "It was a duplicate payment, isn't that exactly what recalls are for?" (event-004).
- **Documents the customer supplied (not bank records):**
  - `attachments/agency_statement_extract.txt`: an Oakfield PM statement line dated 15/08/2026: "Contractor payment – Co-Clean Services Ltd – inv 4471 end of tenancy clean −£651.00".
  - `attachments/coclean_refund_agreement.eml`: an email from Co-Clean ("Dean") dated 17 Sep 2026 at 14:05. It confirms Co-Clean received £651 from Linda on 12 Aug and £651 from Oakfield PM on 15 Aug, and says: "We'll refund £651 to you on our next payment run."

## 2. Evidence and gaps
- **Established by bank records:**
  - One completed £651 Faster Payment from her account to Co-Clean, which the beneficiary bank received (event-001, payment confirmation PDF).
  - The account view shows no second £651 debit to Co-Clean (event-001).
- **Supported only by documents the customer supplied:**
  - The 15 Aug payment by Oakfield PM, made from the agency's landlord funds and not from her account with us (agency statement extract).
  - Co-Clean's written agreement to refund (forwarded email).
  - The bank has not verified either document. The plan treats them as the customer's evidence, and the reply describes the agency payment as "according to the agency statement you sent".
- **Small difference in wording:** the event-001 note says she "spoke to" Co-Clean on 17 Sep, while the attachment is an email dated 17 Sep. Both say the same thing: Co-Clean agreed to refund, with no date given.
- **Gaps the plan records:**
  - The evidence doesn't show the date of Co-Clean's next payment run, or whether the refund has been sent.
  - No bank recall procedure or eligibility rules were supplied. So the reply doesn't refuse a recall on policy grounds. It only explains how a recall works and why it is unlikely to be faster here.

## 3. Why this plan
**Step s1: reply to the customer (the only step).**
- **Explanation:**
  - The confirmation shows a completed payment that the beneficiary bank received, and the account view shows a single debit.
  - The second payment came from the agency, according to the customer's statement extract.
  - Co-Clean has acknowledged the double payment in writing and agreed to refund £651, with no date.
  - So the evidence already answers her question. A recall is only a request that depends on the recipient agreeing, and Co-Clean has already agreed.
- **Evidence cited:** event-001, event-002, event-004, `payment_confirmation_2026-08-12.pdf`, `agency_statement_extract.txt`, `coclean_refund_agreement.eml`.
- **Decision rules applied:**
  - State only the payment stage the record proves.
  - A recall request is not a completed return.
  - Don't promise arrival times or outcomes without a commitment that applies.
  - Similar payments are not automatically duplicates on the same account.
- **Where the rule comes from:** `skill:payments`. This is a handling rule from the payments skill, not a supplied bank policy and not a cited legal obligation. The reply therefore gives no policy or legal reason. It explains the mechanics: a recall asks the receiving bank to contact the recipient, and the money comes back only if the recipient agrees.
- **How this answers her question (event-004):** from her side this was a duplicate. On her account, though, there is a single payment. The duplication arose because the agency paid separately. The recipient has already agreed to refund, which is the outcome a recall would be asking for anyway.
- **Practical suggestions in the reply:**
  - Ask Co-Clean for the date of their next payment run and confirm her refund account details.
  - Tell Oakfield PM so the agency doesn't chase the same refund.
  - These are suggestions to the customer. They are not bank operations.
- **Authorisation:** identity/authority is marked "not_needed". The reply gives information only and changes nothing on the account. The plan raises no safety concerns and sets no escalation triggers.

## 4. Execution boundaries
- The only proposed operation is s1: sending the chat reply above to Linda Ferris. It has no prerequisites and no conditions, and it has **not been sent**.
- The plan does not raise a recall, contact Co-Clean's bank or Oakfield PM, or change anything on the account.
- The plan stops at this explanation. It does not cover what happens if the customer replies or still insists on a recall. That would need a fresh decision, and this memo does not propose one.

## 5. Expected result and limits
- **What s1 could achieve:** Linda would get a clear explanation of:
  - the status of her payment,
  - why only one of the two payments is on her account with us,
  - what a recall can and can't do,
  - why waiting for Co-Clean's agreed refund, and chasing them for a date, is likely the quicker route.
  If the reply is sent, the expected disposition is **completed**.
- **Still unconfirmed:**
  - whether or when Co-Clean will send the refund,
  - the date of their next payment run,
  - that the agency statement and the Co-Clean email are genuine (the customer supplied both).
- **The reply must state:**
  - The payment completed and the beneficiary bank received it.
  - Her account shows only one £651 payment to Co-Clean. The second was Oakfield PM's 15 Aug payment, according to her statement.
  - A recall is a request, not a reversal, and depends on the recipient agreeing.
  - Co-Clean has already agreed in writing, so a recall is unlikely to be faster.
  - We can't confirm the refund has been sent or when it will arrive.
- **The reply must not:**
  - Say the bank can reverse the payment by itself.
  - Promise a recall would succeed or be faster.
  - Say or imply the refund has been sent or has a date.
  - Call this fraud, a scam or a bank error.
  - Give an invented policy as the reason.
  - Describe the agency's payment as a debit from her account with us.
