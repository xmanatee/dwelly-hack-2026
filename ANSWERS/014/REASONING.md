## 1. Situation and history

Tomás Ribeiro, personal current account holder at Harrow & Vale Bank plc, contacted the bank on 2026-09-16 through the authenticated in-app personal banking chat (event-002). He reports that a holding deposit for a flat "went through twice", £634 each, that the letting agency promised a refund in 5–10 working days two days earlier, and that he needs the money for the actual deposit. He asks the bank to "just do a chargeback on the second one now" and says he has read that he is entitled to it. After the servicing agent confirmed seeing both payments and offered to explain how a chargeback would work and whether it is the fastest route (event-003), the customer replied that he does not want to wait 10 days for the agency (event-004).

Authenticated bank records (event-001, internal account view; `attachments/card_transactions.csv`) show two debit card payments to PAYGATE*NORTHGATE LET (MCC 6513, real estate agents): 2026-09-11 18:02:37, £634.00, auth A71C02; and 2026-09-11 18:04:12, £634.00, auth A71C09. Both have status "settled 2026-09-13". No PAYGATE refund credit appears in the snapshot.

The customer's own account (event-001, event-002) is that he clicked the agency's payment link twice after a "page not responding" message — i.e. both payments were initiated by him. This is the customer's report, consistent with the two distinct authorisation codes in the bank record.

The customer forwarded an agency email (`attachments/agency_refund_email.eml`) from Northgate Lettings (accounts@northgate-lettings.example, signed "Nicole"), dated Mon 14 Sep 2026 15:22:10 +0100, subject "RE: Holding deposit paid twice - 9 Lime Grove". It acknowledges the duplicate £634.00 holding deposit taken on 11 September and states the agency's payments team "will refund one payment to the card it was paid from within 5-10 working days", visible as a refund from PAYGATE.

The full input is saved in `context.md`.

## 2. Evidence and gaps

**Established from the record**
- Two separately authorised, settled payments of £634 each on 11 Sep (`card_transactions.csv`, event-001).
- Both initiated by the customer (event-001, event-002). Neither is unauthorised or fraudulent on the supplied evidence.
- A written merchant refund commitment dated 14 Sep with a 5–10 working day window (`agency_refund_email.eml`). As at 16 Sep, that window has not elapsed, and no refund shows on the card record (`card_transactions.csv`).
- Identity: the customer is interacting through the authenticated in-app chat and the internal account view identifies him as the account holder (event-001, event-002). Identity authority is established.
- No dispute has been raised in the supplied record (event-003 only offers an explanation).

**Not established / missing**
- Harrow & Vale Bank's card dispute policy and the applicable card-scheme rule on raising a duplicate / "credit not processed" dispute while the merchant has already committed in writing to a refund and the refund window is still running. This is not supplied, so eligibility cannot be decided at the servicing stage.
- Whether any PAYGATE refund has posted after the transaction snapshot.
- Any bank-committed dispute-processing timescale (none supplied), so no timing can be promised.
- The customer's belief that he is "entitled" to a chargeback (event-002) is his understanding, not a rule in the supplied material; the record neither confirms nor denies it.

**Contradictions:** none in the facts. The tension is between the customer's expectation (immediate chargeback) and the record (self-initiated duplicate, merchant refund already promised and still within its window).

## 3. Why this plan

**s1 — Request Card Disputes team action.** The customer has made a clear dispute request. The record identifies the exact transaction (date/time, amount, merchant, MCC, auth code A71C09, settlement date) and the supporting evidence (customer's duplicate-click statement; the agency's 14 Sep email; absence of a refund at 16 Sep). What is missing is the eligibility rule: whether a duplicate/credit-not-processed dispute may be raised now or must wait for the merchant's refund window to expire. The plan's criterion (source: skill:payments handling rule, not a supplied bank policy or legal obligation) is to identify the transaction precisely, treat a refund promise as not a completed refund, and request the named team's action for a material gap rather than guess eligibility or outcome. Referring the request with full evidence lets the responsible team apply the scheme rules and bank policy that the planner does not have. The instruction expressly bars presenting this to the customer as a raised chargeback until the team acknowledges.

**s2 — Reply to the customer.** The customer believes he is entitled to an immediate chargeback and does not want to wait (event-002, event-004). The reply must (a) state what the record proves — two separately authorised payments, both settled 13 Sep, the agency's written commitment and the fact its window has not passed and no refund is visible; (b) correct the expectation that a chargeback is an instant, guaranteed or necessarily faster refund, without asserting either an entitlement or a denial; (c) report the dispute referral as pending, not raised; and (d) give practical steps (keep the email, watch for a PAYGATE refund, contact the agency to expedite). The criterion (skill:payments handling rule) is to state only the stage the record proves, promise no arrival times absent an applicable commitment, and report a planned operation as pending until its execution is acknowledged.

**Order.** s2 requires s1 because the customer reply describes the referral; the wording must match the actual status of s1. Until s1 is acknowledged, the message must say the request is being passed / pending, not that it has been passed. The plan's own draft uses "I have passed your request"; that wording is held back as a NOT SENT draft until s1 is acknowledged (see future_messages).

**Alternatives.** Raising a chargeback immediately at the servicing level is not supported: eligibility rules are not supplied and the merchant has already committed in writing to refund within a window that is still running. Simply declining and telling the customer to wait is also not chosen, because the customer has made a legitimate dispute request and the bank has a dedicated team to assess it. The plan takes the middle path: refer with full evidence, manage expectations honestly.

## 4. Execution boundaries

- s1 is a request to the Card Disputes team to log and assess; it is not a raised chargeback. Whether a dispute is raised, and when, is the team's decision.
- s2 depends on s1. The customer message may only describe the referral as completed after s1 is acknowledged; otherwise it stays in pending language.
- The plan stops after s2. The next step depends on new information: the Card Disputes team's assessment result (to be reported to the servicing agent for onward communication) or a PAYGATE refund posting to the card. Neither outcome is predicted here. If s1 cannot be executed, a fresh decision is needed rather than an alternative route invented at this stage.
- No safety flags; no escalate-if conditions in the plan.

## 5. Expected result and limits

**What the steps could achieve:** the dispute request reaches the team able to assess it under the applicable rules, with the complete evidence pack; the customer receives an accurate picture of both payments, the agency's commitment, and what a chargeback is and is not, and knows what to watch for and whom else to contact.

**What remains unconfirmed:** whether a dispute can be raised now or only after the refund window expires; whether the agency's refund will arrive, and when; any dispute outcome or credit date; whether a chargeback would be faster than the agency refund.

**Constraints preserved:** the message states the five must-state points (separately authorised payments with different auth codes, settled 13 Sep; agency's written 5–10 working day commitment not yet elapsed and no refund visible; chargeback is a team-assessed scheme dispute with no promised timing or guarantee; dispute request pending with nothing raised or credited; keep the email, watch for PAYGATE refund, may contact the agency). It does not assert legal entitlement or a bank obligation to refund, does not promise an outcome, date or speed, does not describe either payment as unauthorised or fraud, does not claim the dispute has been raised or a refund received, and does not request PINs, passwords, card numbers or one-time codes.
