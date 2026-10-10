# REASONING — Case 001: Marcus Bell, £750 hold following Meridian APP-scam recovery request

Full input is saved in `context.md`. This memo sets out the public grounds for the plan of record; it does not change its decision, disposition or actions.

## 1. Situation and history

**Authenticated bank records (event-001, `attachments/account_hold_notice.txt`):**
- 21 Sep 2026 14:10 — Faster Payment credit of £2,600.00 from "L FARRELL" (Meridian Bank), reference "VAN".
- 21 Sep 2026 16:40 — Debit of £1,850.00 to "BARCLAYCARD", the customer's own card, a payee on file since 2022.
- 23 Sep 2026 17:55 — Inbound interbank funds-recovery request from Meridian Bank Fraud Operations, ref MER-FR-2026-081734 (`attachments/funds_recovery_request_MERIDIAN.txt`): payer reports the £2,600 as an authorised push payment scam, category "Purchase scam – goods not received (vehicle)". Payer statement summary: paid for a Transit seen online, seller said delivery Tuesday, no van, seller not answering. No police reference. No previous reports against the payee account.
- 23 Sep 2026 17:56 — System hold of £750.00 applied (all available funds; balance £750.00). The record states bank policy: hold the disputed amount still available and respond to the sending bank within 2 working days.
- Profile: 6-year relationship, no fraud markers, no contact in 12 months, no other inbound credits from unknown parties in 90 days.

**Today's call, 24 Sep 2026 (contact start 09:20; individual event times not recorded):**
- event-002 — Customer passes ID&V and asks why £750 is held; says he cannot pay rent tomorrow.
- event-003 — Agent raises the £2,600 payment from L Farrell.
- event-004 — Customer's report: sold his old Transit via a marketplace; the buyer collected it Monday (21 Sep) and paid by transfer while standing on his drive; he has the messages, listing and V5 handover; he used most of the money to pay off his credit card.
- event-005 — Agent acknowledges.
- event-006 — Customer demands release; rent is £900, due tomorrow (25 Sep).

**Customer-supplied exports (not bank-verified):**
- `attachments/customer_evidence_listing.txt` — Ford Transit Custom 2017, £2,600, listed 12 Sep, Reading, "Collection only… No delivery", status SOLD (marked 21 Sep 2026). Seller "Marcus B.", member since 2019, 14 reviews.
- `attachments/customer_evidence_messages.txt` — chat with buyer "Lou F.": 19 Sep arranges to view Monday 2pm; 21 Sep 13:52 "Here, parked outside no 14"; 14:06 "sending the money now by bank transfer, ref VAN"; 14:11 seller confirms V5C green slip filled in and both sets of keys handed over; 14:12 buyer "Cheers mate".

The customer's report (event-004) and his exports describe an in-person collection; the authenticated interbank record (`funds_recovery_request_MERIDIAN.txt`) carries the payer's contrary account. Neither the chat nor the listing is a bank record.

## 2. Evidence and gaps

**What the records support:**
- Identity: ID&V passed on the phone channel (event-002); the caller is the account holder (event-001). Identity authority is established.
- The hold is a system action triggered by the Meridian request, applied per the policy stated in the bank's own record (event-001, `account_hold_notice.txt`), and equals all available funds (£750).
- The timing in the customer's chat export (payment sent 14:06, ref VAN) is consistent with the authenticated credit (14:10:07, ref VAN). The listing's "collection only" wording is consistent with his account and inconsistent with the payer's "delivery Tuesday" statement.
- £1,850 of the £2,600 was spent to a long-standing own-card payee two days before the request arrived — consistent with ordinary use of sale proceeds, though it also means only £750 is recoverable regardless of outcome.
- Risk profile is low on record: 6 years, no fraud markers, no other unknown-party credits, no previous reports against the account.

**Contradictions and what cannot be established:**
- The payer's statement (vehicle to be delivered, not received) and the customer's account plus exports (collected in person, keys and V5C slip handed over) directly conflict. Nothing in the supplied records resolves this.
- The marketplace buyer "Lou F." and the payer "L FARRELL" are plausibly the same person but this is not established by any bank record.
- The customer says he has V5 handover evidence (event-004) but no V5C/DVLA document is among the attachments. This is the one item that could independently corroborate a completed in-person sale and the buyer's identity.
- Meridian supplied no police reference.
- Fraud Operations has not yet made any decision; the reply to Meridian is outstanding.
- Only day precision is recorded for today's call events.
- It is unknown whether any other funds or income are expected before 25 Sep.

The customer's exports are credible on their face but are self-supplied and editable; they are evidence for Fraud Operations to weigh, not grounds for an agent to overturn a policy hold on the call.

## 3. Why this plan

**s1 — Maintain the hold, decline agent-level release.**
The hold was applied by the system under the bank policy recorded in event-001 and the hold notice ("place a hold on the disputed amount still available, respond to the sending bank within 2 working days"). This is a supplied bank policy, not a legal citation. The customer's evidence contradicts the payer's statement, and that conflict is unresolved; the decision criterion is to hold identified disputed funds pending the responsible team's review and to name the conflict rather than guess at it. The plan also constrains proportionality: the hold is the £750 already held and must not be extended to any other account function. Source as recorded: `evidence:event-001`.

**s2 — Urgent referral to Fraud Operations.**
The Meridian request is addressed to Harrow & Vale Fraud Operations (`funds_recovery_request_MERIDIAN.txt`), so both the hold decision and the interbank response sit with them. The plan's criterion (from the fraud-takeover skill's handling rule, not a bank policy or legal duty) is that a recovery request is an allegation, not proof, and not a completed return; and that essential-living-cost hardship is to be referred to the appropriate team rather than met with blanket refusal. The referral therefore carries both sides: the customer's account and exports (event-004, listing, chat), the timing match between chat and credit, the pre-request spend to his own Barclaycard, the clean profile, the unresolved conflict with the payer's statement, and the hardship (£900 rent due 25 Sep with all available funds held — event-006). It asks for prioritisation given the rent deadline and the 2-working-day response window, and for Fraud Operations to decide retain / part-release / release and notify the customer by his registered phone contact. The plan does not pre-judge that decision.

**s3 — Ask for the V5C/DVLA sale evidence.**
The customer states he holds V5 handover proof (event-004) but it is not in the supplied attachments. It is the single missing item most capable of independently corroborating in-person collection and identifying the buyer. The criterion is to request only the specific fact that could change the decision and to use a secure route (document upload or secure message, not details read over the phone). The plan confirms the exports already on file need not be re-sent. Source: general evidence-handling practice.

**s4 — Reply to the customer.**
The customer is verified and entitled to know why the funds are held, what has and has not been decided, what he can do, and the realistic rent position. The scripted reply is drawn from the hold notice, event-001 and the Meridian request (nature of the dispute only) and honours the hardship flag with an offer of referral to the financial support team and a prompt to speak to his landlord. It avoids promising release, any timing, or any outcome, and it does not quote the payer's statement verbatim or share their identifiers. Source: planner.

**Order and dependencies.** s1 states the present position so the referral and reply are accurate. s2 is the substantive next move and should be made today given the 2-working-day window from 23 Sep 17:55 and the 25 Sep rent date. s3 and s4 are delivered on the call; s3 feeds the s2 review when the document arrives. No step requires another to complete first.

**Alternatives considered within the plan.** Agent-level release was rejected because the hold is a policy action tied to a live interbank request and the factual conflict is unresolved on bank records. A broader restriction was rejected as disproportionate: the risky operation is the disputed credit, nothing else on the account is implicated (no fraud markers, no other unknown-party credits). The plan does not introduce any other strategy.

## 4. Execution boundaries

- No solver tools or bank execution are connected; every step is a proposal. Nothing has been held anew, referred, requested or said yet.
- s1 is confined to the existing £750 hold on SYN-ACCT-01-1 under MER-FR-2026-081734. It does not add, extend or alter any restriction.
- s2 is a referral only. The decision to retain, part-release or release, and the response to Meridian, belong to Fraud Operations. The plan stops there pending their decision.
- s3 depends on the customer choosing to upload the document; if he does not, the referral proceeds on the evidence already on file.
- s4 is scripted for delivery on the current call. The referral to the financial support team is an offer the customer may accept; it is not a separate proposed operation in this plan.
- If any step cannot be executed as proposed (e.g. Fraud Operations declines urgency, or the customer cannot upload), that is a blocked execution requiring a fresh decision, not an alternative invented here.

## 5. Expected result and limits

**What the steps could achieve:** the hold remains proportionate and correctly scoped; Fraud Operations receives a complete, balanced referral today with the hardship flagged and the deadline noted; the customer understands the position, knows exactly what to send and how, and is pointed to hardship support.

**What remains unconfirmed:** whether the £750 will be released in whole or part, and when; whether Meridian's claim is upheld; whether "Lou F." is L Farrell; whether the V5C/DVLA evidence exists and what it shows; whether the customer has any other means to meet rent on 25 Sep. Even a full release would leave a £150 shortfall against the £900 rent — the plan states this plainly to the customer.

**Constraints preserved (must_state):** the hold's cause and date (automatic, 23 Sep, formal recovery request, van payment reported as goods not received); that policy requires the available disputed funds to be held and the agent cannot release them; that his account and exports go to the fraud team as evidence in his favour and no decision has been made; the 2-working-day response obligation with no promised outcome or timing; that the hold is limited to the £750 and is not a fraud marker; the rent shortfall, financial support referral and landlord suggestion; and the single evidence request via a secure channel.

**Constraints preserved (must_not):** no promise or implied release or date; no suggestion the customer is a scammer or the payer is lying; no disclosure of the payer's identifiers, Meridian internals beyond the fact and nature of the dispute, or the payer's statement verbatim; no widening of the hold or suggestion other functions are restricted; no claim the agent decides the hold; no promise to cover rent, no high-cost borrowing, no outcome on Meridian's claim; no statement that any referral or review has already happened.
