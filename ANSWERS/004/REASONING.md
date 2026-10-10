# Decision memo: case 004, "Two rent payments in one month"

The full input is saved in `context.md`. Everything below is proposed. Nothing has been carried out.

## 1. Situation and history
All events are dated 2026-09-04. Individual times are not recorded.

**Bank records:**
- **event-001** (internal account view) shows Priya Desai's personal current account with two payments:
  - a **£1,000 standing order** on 1 Sep to HARROW & VALE RE HARBOUR LETS LTD CA, ref "RENT 27 ELM RD", set up Feb 2025, paid on the 1st of the month
  - a **£900 Direct Debit** on 3 Sep to H&V COLLECT / HARBOUR LETS, with the mandate "created 20 Aug 2026 via originator invite"
- event-001 also says the originator's advance notice was sent on 24 Aug, that the collection amount matches the notice, and that the standing order is still active for 1 Oct.
- `attachments/statement_extract_sep.csv` confirms both debits: −1000.00 on 2026-09-01 and −900.00 on 2026-09-03, ref HL-27ELM-0091.
- `attachments/standing_order_on_file.json` confirms the standing order is active, £1,000 monthly, next payment 2026-10-01, created 2025-02-01.

**Originator document:** `attachments/dd_advance_notice_2026-08-24.eml` is from "Harbour Lets via H&V Collect", dated 24 Aug 2026 and addressed to priya.desai@example.net. It says:
- first collection £900.00 on or around 3 September 2026, then £900.00 monthly
- cancel any rent standing order before the first collection to avoid paying twice
- the Direct Debit Guarantee applies

It also says "You have set up a Direct Debit". That is the originator's statement, not a bank record that she authorised the mandate.

**Customer's account (her statements, not verified records):**
- **event-002 / request:** her rent was taken twice; she wants the £900 refunded under the Guarantee today and the Direct Debit cancelled; she never agreed to £900 and her rent is £1,000.
- **event-003:** the agent offered to explain "what the options are".
- **event-004:** she rejected options and said the Guarantee means an immediate refund if there is an error, and that this is an error.

She is the account holder, writing in the authenticated in-app chat (event-001, event-002). The plan records her identity and authority as established.

## 2. Evidence and gaps
**What the records show:**
- The £900 collection matches the advance notice in amount and date (event-001, the .eml).
- The £1,000 standing order and the £900 Direct Debit are separate instructions, both paying Harbour Lets.
- The notice itself warned about paying twice if the standing order stayed active.

**What cannot be established from the supplied material:**
- Whether she completed or authorised the 20 Aug setup. The record says only "via originator invite" (event-001).
- Whether she received the 24 Aug notice. The address on the .eml is not confirmed as hers anywhere else.
- The agreed rent. She says £1,000 (event-002); the notice says £900; nothing supplied settles it.
- The outcome of the cancellation and of the Guarantee review. Neither has been carried out.

**Conflicting accounts:** Her statement that she "never agreed to £900" conflicts with the notice's "You have set up a Direct Debit". The plan does not resolve this and sends it to the claims team.

**Guarantee terms:** No full Guarantee wording and no bank policy were supplied. The only reference to the Guarantee is the line in the notice saying it applies. Her description of it (event-004) is her own statement and has not been checked against any supplied text.

## 3. Why this plan
**s1: cancel the mandate (Direct Debit servicing team)**
- **Why:** The account holder gave a clear instruction to cancel (event-002). Cancelling affects only future collections and does not settle the refund.
- **Evidence:** event-002, event-001.
- **Decision criterion:** act on the account holder's clear instruction about future payments, and keep cancellation separate from any Guarantee claim or reversal of a payment already taken.
- **Rule source:** skill:scheduled-payments, a handling rule rather than a supplied bank policy or a legal obligation.
- **Scope:** The instruction says not to reverse the £900 under this request and not to touch the standing order. She did not ask to change the standing order.

**s2: Guarantee claim (Direct Debit Guarantee claims team)**
- **Why:** She has made a Guarantee claim. The records show the collection matched the notice, but her statement that she never agreed to £900 is unresolved. The claims team must decide; the chat agent cannot approve or refuse the claim.
- **Evidence:** event-002, event-004, event-001, the .eml.
- **Decision criterion:** identify the claimed error and send it to the right review route, without promising a refund for every dispute with a supplier.
- **Rule source:** skill:scheduled-payments, a handling rule.
- **What the claims team gets:** the matching records and the unknowns, so they can assess both sides.

**s3: reply to the customer (requires s1 and s2)**
- **Why:** She needs the recorded facts, what has been requested and what is still unconfirmed. These must be stated directly, not as options; she rejected options in event-004.
- **Evidence:** event-001, event-004, the .eml, standing_order_on_file.json.
- **Decision criterion:** report recorded status without claiming execution or an outcome, keep changes to future payments separate from the refund claim, and explain how to complain.
- **Rule source:** skill:complaints-rights, a handling rule.
- **Order:** It depends on s1 and s2, so it can truthfully say what has been requested. The plan's own wording assumes both have been acknowledged ("I have passed…", "I have also asked…"). For that reason it is kept only as a NOT SENT draft linked to s1 and s2. Even then, the cancellation must be described as requested and pending unless s1 is confirmed done, and the claim reported as passed for review only if s2 has been acknowledged.

**s4: ask whether she completed the 20 Aug setup (requires s3)**
- **Why:** The record shows only that the mandate came from the originator's invitation. Whether she authorised it is the key unknown for deciding whether there was an error.
- **Evidence:** event-001, event-002.
- **Decision criterion:** when a gap affects the decision, ask the customer for that one specific fact.
- **Rule source:** general:evidence, a general handling principle.
- Her answer is to be added to the s2 claim.

**Refund today:** The plan does not offer one. The £900 matches the notice, so an error is not shown on the records, and only the claims team can decide the claim.

## 4. Execution boundaries
- s1 and s2 are separate team requests with no dependency on each other. Both are pending.
- s3 waits for s1 and s2. s4 waits for s3.
- The plan stops at handing over and asking for information. It does not decide the claim, reverse the £900, change the standing order or settle the rent dispute.
- The plan sets no escalation triggers and no conditional branches.
- If s1 or s2 cannot be carried out, a new decision is needed. This memo does not offer another strategy.

## 5. Expected result and limits
**What the steps could achieve:**
- A cancellation request for HL-27ELM-0091, stopping future £900 collections once confirmed.
- A registered Guarantee claim with the full record, including her statement.
- A clear status message to the customer.
- Her answer on whether she set up the mandate, added to the claim.

**What stays unconfirmed:**
- Whether the cancellation has been done.
- The claim outcome and any refund.
- Whether she authorised the mandate or received the notice.
- The agreed rent.

**The customer message must state:**
- the £900 matches the 24 Aug notice, so an error cannot be confirmed and no immediate refund can be promised
- the claim, including her statement that she never agreed to £900, is passed for review and the result is unknown
- cancellation has been requested and is not confirmed
- cancelling stops future collections but does not reverse the £900 or change her arrangement with Harbour Lets
- the £1,000 standing order is still active for 1 Oct and has not been changed
- she can contact Harbour Lets about paying twice
- she can make a complaint

**The message must not:**
- promise or suggest a refund
- claim the cancellation or claim registration is done before confirmation
- state that she authorised the mandate or received the notice
- refuse the claim outright or say the Guarantee can't apply
- change the standing order
- give tenancy or legal advice, or decide what rent she owes
- give her a list of options
