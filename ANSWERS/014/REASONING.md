# Decision memo: case 014, duplicate holding-deposit payment

The full input is in the saved `context.md`. Nothing below has been carried out. All actions are proposed and pending.

## 1. Situation and history

**Authenticated bank records**
- **event-001** (internal account view, 16 Sep 2026): Tomás Ribeiro has a personal current account with a debit card. The view shows two −£634.00 payments to PAYGATE*NORTHGATE LET on 11 Sep, at 18:02 and 18:04.
- **`attachments/card_transactions.csv`** gives the detail:
  - 2026-09-11 18:02:37, auth A71C02
  - 2026-09-11 18:04:12, auth A71C09
  - Both have MCC 6513 (real estate agents) and both settled on 2026-09-13.
  - No PAYGATE refund line appears.

**What the customer reports and supplies**
- **event-001** also records his account: he clicked the agency's payment link twice after a "page not responding" message.
- **`attachments/agency_refund_email.eml`**: an email from Northgate Lettings, dated Mon 14 Sep 2026 15:22, forwarded by the customer. It says: "we can see the duplicate holding deposit of £634.00 taken on 11 September", promises to refund one payment to the card within 5–10 working days, and says it will show as a refund from PAYGATE.
- **event-002** (chat, 16 Sep): he asks the bank to "just do a chargeback on the second one now". He says he needs the money for the actual deposit and has "read that I'm entitled to it".
- **event-003**: the agent confirms they can see both payments and offers to explain whether a chargeback is the fastest route.
- **event-004**: "I don't want to wait 10 days for an agency to get round to it."

**Identity and authority:** treated as established. He is a customer in authenticated in-app personal banking, asking about his own account (event-001, event-003, request.md). No safety flags were raised.

## 2. Evidence and gaps

**What the evidence supports**
- **Duplicate payment:** same merchant, same amount, 95 seconds apart, different auth codes, both settled (CSV). The merchant admits the duplicate in writing (email).
- **Customer-authorised payments:** he says he made both clicks himself (event-001). So this is a duplicate-payment issue, not an unauthorised or fraudulent one.
- **Refund promised, not received:** the agency has promised a refund, but the supplied records show no refund (CSV). A promise is not a booked credit.

**Minor wording difference:** the event-001 note paraphrases the email as "will refund £634". The email itself says "refund one payment". These are consistent, and the plan uses the email's wording.

**What cannot be established**
- **The bank's chargeback or dispute rules and timescales** for a duplicate payment where the merchant has promised a refund. None were supplied. So eligibility, timing, and whether a chargeback would beat the agency's 5–10 working days cannot be confirmed. The customer's belief that he is entitled to one cannot be checked against any supplied policy.
- **Whether the merchant refund is under way** after the date of the supplied records.

## 3. Why this plan

### s1: request card disputes team action (target: card disputes team, Harrow & Vale Bank plc)
- **Explanation:** the customer asked for a chargeback and the records support a duplicate. But no bank chargeback policy was supplied, and the merchant has already promised a refund. Eligibility and timing must be decided by the team that handles card disputes, not promised in chat.
- **Evidence:** event-002, event-004, `card_transactions.csv`, `agency_refund_email.eml`.
- **Criterion:**
  - Identify the exact transaction by reference, amount, date and parties. That is why the instruction names auth A71C09 at 18:04:12 as the disputed payment, and A71C02 at 18:02:37 as the matching one.
  - A promised refund or recall is not a completed return.
  - Do not promise outcomes or arrival times without an applicable commitment.
- **Source:** `skill:payments`. This is a handling rule from the skill, not a supplied bank policy or a cited legal obligation.
- **Instruction to the team:** it asks the team to take the pending merchant refund into account so the customer is not credited twice. That risk follows directly from the agency's email.

### s2: reply to the customer (requires s1)
- **Explanation:** the reply gives the status the records actually show, says what has not been confirmed, and sets out the next step without promising an outcome or a date.
- **Evidence:** the same four sources as s1.
- **Criterion:** state only what the supplied record proves. A promised merchant refund is not a booked credit. Do not promise arrival times without an applicable commitment.
- **Source:** `skill:payments`.
- **Order:** the reply comes after s1 because it reports the referral. It may say "I've passed" only once s1 is confirmed as done. Until then it must say the referral is pending.

### Alternatives not chosen
- **Raising a chargeback directly in chat:** not done, because no applicable policy or authority was supplied.
- **Telling the customer to just wait for the agency:** not chosen, because it would ignore his explicit request.
- **Escalation:** the plan picks escalation as the course that is supported. It adds no other strategy.

## 4. Execution boundaries
- **Dependency:** s1 must be carried out and confirmed first. s2 depends on it.
- **Where the plan stops:** after the referral and the customer reply, pending the disputes team's decision. The plan has no escalate-if conditions or conditional branches, and none are added here.
- If s1 cannot be carried out, the reply must not claim the referral was made. A new decision would be needed.
- The text that uses "I've passed" is kept as a separate, unsent draft, to be used only after s1 is confirmed.

## 5. Expected result and limits

**What the plan could achieve**
- A referral that gives the card disputes team the exact transaction details, both attachments, and the double-credit risk.
- A clear, honest status update for the customer.

**What it does not achieve or confirm**
- Any chargeback, credit, timeline, or that a dispute would be faster than the agency's refund. These remain unconfirmed.

**The reply must state:**
- The bank can see two settled £634.00 payments to PAYGATE*NORTHGATE LET on 11 Sep, about two minutes apart.
- The agency's 14 Sep email admits the duplicate and promises a refund within 5–10 working days. That timescale is the agency's, not the bank's.
- No refund shows in the records available now.
- His chargeback request has been passed (or, before s1 is confirmed, is being passed) to the card disputes team for review. Whether a chargeback can be raised, and how long it would take, is not confirmed.
- He should tell the bank if the PAYGATE refund arrives, so the duplicate is not reclaimed twice.

**The reply must not:**
- Say he is entitled to a chargeback or that it will succeed.
- Promise an immediate reversal, a credit date, or that a chargeback will be faster than the agency refund.
- Say a chargeback has been raised or that money has been or will be returned.
- Say the agency refund has been processed or received.
- Call either payment unauthorised or fraudulent.
- Invent a chargeback policy, scheme rule or timeframe.
