# Decision memo: Case 001, £750 hold after an inbound funds-recovery request

The full input is saved in `context.md`. This memo explains the plan of record. It does not change it. All actions are still proposed. Nothing has been executed.

## 1. Situation and history

**Authenticated bank records:**
- **event-001** (internal account view, 24 Sep 2026) and **attachments/account_hold_notice.txt** show:
  - **21 Sep 14:10:** a £2,600 Faster Payment arrived from "L FARRELL" (Meridian Bank) with reference "VAN".
  - **21 Sep 16:40:** £1,850 was paid to BARCLAYCARD, a payee on file since 2022.
  - **23 Sep 17:55:** Meridian's funds-recovery request arrived.
  - **23 Sep 17:56:** the system applied a hold of £750, which is all available funds. Balance £750, hold £750.
  - The customer has been with the bank 6 years, has no fraud markers, no contact history in 12 months and no other inbound credits from unknown parties in 90 days.
- **attachments/funds_recovery_request_MERIDIAN.txt** (ref MER-FR-2026-081734, received 23 Sep 17:55:12):
  - The payer reported the payment on 23 Sep at 16:40 as a purchase scam where goods were not received.
  - The payer's summary says: "Seller said it would be delivered Tuesday. No van, seller not answering."
  - Meridian asks H&V to hold the remaining funds and return them, and to respond within 2 working days.
  - No police reference was supplied, and there are no previous reports against the payee account.

**What the customer said on the call** (phone, 24 Sep, contact started 09:20):
- **event-002:** he passed ID&V. He has no access to his money and his rent is due tomorrow.
- **event-004:** he sold his old Transit on a marketplace, the buyer collected it on Monday and paid by transfer on his drive, and he has "the messages, the listing, the V5 handover". He used most of the money to pay off his credit card.
- **event-006:** he wants the money released. His rent is £900 and due tomorrow.
- At **event-003** the agent mentioned the payment from "L Farrell". At **event-005** the agent acknowledged his explanation.

**Evidence the customer exported (not verified by the bank):**
- **attachments/customer_evidence_listing.txt:** a 2017 Ford Transit Custom at £2,600, listed 12 Sep, "Collection only… No delivery", marked SOLD on 21 Sep 2026.
- **attachments/customer_evidence_messages.txt:** buyer "Lou F." arranged a Monday viewing. On 21 Sep she was "parked outside" at 13:52 and said at 14:06 she was "sending the money now… ref VAN". At 14:11 the seller confirmed "V5C green slip filled in, you've got the keys".

## 2. Evidence and gaps

- **Conflict between accounts.** The payer's account (promised Tuesday delivery, no van) conflicts with the customer's account and exports (collection only, keys and V5C slip handed over at about the time the payment arrived at 14:10). The bank has not verified the exports. The plan does not settle the conflict. It passes it to the team that owns the review.
- **What supports the customer's version.** The timing fits: the chat says payment was being sent at 14:06 and the credit arrived at 14:10:07. The amount and reference "VAN" also match. However, these items come from the customer's own exports.
- **Gaps recorded in the plan:**
  - The V5C/DVLA change-of-keeper evidence he mentioned has not been supplied.
  - Fraud Operations has not recorded any decision or reply to Meridian.
  - It is not confirmed that "Lou F." and "L FARRELL" are the same person.
  - It is not known whether he has any other way to pay tomorrow's £900 rent.
- **Things the plan does not determine:**
  - The exact calendar date of the 2-working-day deadline.
  - Whether the £1,850 Barclaycard payment has any bearing on the dispute. The message must not suggest it does.

## 3. Why this plan

- **s1: keep the hold and do not release it on this call.**
  - *Explanation:* the hold followed an inbound recovery request for the disputed £2,600. If a servicing agent released it, that would bypass the bank's review and the reply owed to the sending bank.
  - *Evidence:* event-001, account_hold_notice.txt, funds_recovery_request_MERIDIAN.txt.
  - *Criterion:* when there is an inbound recovery request, hold the disputed amount still available and respond to the sending bank within 2 working days.
  - *Source:* the **bank policy stated in the case record** (evidence:event-001). This is supplied bank policy, not a legal obligation cited by the plan.
  - The plan also says not to widen restrictions beyond the existing £750.
- **s2: refer to H&V Fraud Operations.**
  - *Explanation:* the customer's evidence directly contradicts the payer's claim. Fraud Operations owns the recovery request and the reply to Meridian, so it needs this material before the deadline.
  - *Evidence:* event-004, the listing and chat exports, the Meridian request, the hold notice.
  - *Criterion:* pass material evidence and conflicts between records to the responsible team, and do not resolve them by guessing.
  - *Source:* **skill:payments**, a handling rule rather than a bank policy.
  - The referral flags the rent deadline so the review is treated as time-sensitive.
- **s3: ask for the V5C/DVLA proof.**
  - *Explanation:* he said he has the V5 handover, but it is not among the attachments. It would be independent proof that the vehicle changed hands at collection.
  - *Evidence:* event-004, request.md (the attachment list).
  - *Criterion:* ask for the one specific missing piece of evidence that bears on the dispute.
  - *Source:* **general:evidence**.
- **s4: offer a financial support referral.**
  - *Explanation:* an essential cost (rent due tomorrow) is at risk because his only available funds are held. Help with the shortfall is separate from the outcome of the fraud review.
  - *Evidence:* event-002, event-006, event-001. The plan flags `financial_difficulty`.
  - *Criterion:* refer to the support team when essential living costs are at risk, and do not recommend high-cost borrowing.
  - *Source:* **skill:vulnerability-support**.
- **s5: reply to the customer.**
  - *Explanation:* he asked what is going on. The reply gives the recorded reason for the hold, says who is reviewing it, and explains what the call cannot do or promise.
  - *Evidence:* event-001, event-002, event-006, the Meridian request.
  - *Criterion:* give the recorded status and what it does not confirm, and do not promise outcomes or timescales without evidence.
  - *Source:* **general:planner**.
  - Note that the scripted phrase "showing she collected the van" restates his own evidence. The bank has not verified it.

**Order of steps:** s5 depends on s1–s4. The message reports the hold position, the referral, the evidence request and the support offer. It must describe the referrals as being arranged until each one is acknowledged.

## 4. Execution boundaries

- The plan stops at escalation. The decision on the hold and the reply to Meridian rest with Fraud Operations, and nothing about them is recorded yet.
- The financial support referral goes ahead only if the customer agrees (s4).
- The plan has no conditional branches (`escalate_if` is empty).
- If any step cannot be carried out, for example the Fraud Operations referral is not acknowledged, a fresh decision is needed. This memo does not propose another strategy.

## 5. Expected result and limits

**What the plan could achieve:**
- Fraud Operations receives the customer's evidence and the conflict in time for the Meridian reply.
- The customer understands why the hold was applied and is asked for the V5C/DVLA proof.
- He is offered support with his rent.

**What remains unconfirmed:**
- Whether the hold will be released or the funds returned, and when.
- Whether the buyer and the payer are the same person.
- Whether he can pay his rent tomorrow.

**The message must state:**
- The sending bank reported the payment as disputed and asked for the remaining funds to be held, and under policy the available disputed funds are held during review.
- The agent cannot release the hold, and the case is going to Fraud Operations.
- His explanation and evidence will be included in the review.
- A request for the V5C/DVLA confirmation and any other proof of the handover.
- No decision or release time can be promised.
- An offer of a financial support referral.

**The message must not:**
- Promise or suggest release or a timescale.
- Suggest that he committed fraud, or that the payer's claim is true or false.
- Disclose the payer's account details.
- Suggest the £1,850 Barclaycard payment will be reclaimed or is affected.
- Say the bank has already responded to Meridian or decided anything.
- Suggest high-cost borrowing.
- Ask for PINs, passwords or one-time codes.
