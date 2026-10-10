# Decision memo: case 026, Yara Bellune (SYN-ACCT-B026)

The full input is saved in `context.md`. Citations below use event IDs E01–E05 from `history.md`, plus `request.md` and the two attachments.

## 1. Situation and history
- **E01 (2026-11-16 09:00, secure chat):** The bank's contact record says Yara Bellune passed the identity check through the established secure-chat process. That is an authenticated record. She then asked to cancel "the £200 monthly standing order to Sedgepan Club". She said she is not asking to close the account or move the balance.
- **E02 (09:05, internal mandate view):** The register says no legal or operational restriction is recorded. Two attachments were retrieved:
  - `attachments/joint-mandate.pdf`: holders Yara and Orin Bellune, effective 2025-06-02. Either holder may cancel an existing standing order alone. Closing the account is a separate process. No restriction recorded.
  - `attachments/standing-order.csv`: SO-026, payee Sedgepan Club, destination SYN-ACCT-CLUB026, £200.00, next due 2026-11-20, status active.
- **E03 (09:10, customer chat):** Yara asked us not to call Orin Bellune. She said she is frightened Orin will retaliate if told about this conversation, and asked for secure chat rather than a phone callback. This is her own report. Nothing on file confirms or disproves it.
- **E04 (09:15, internal procedure view):** This is the bank's own servicing terms and support directory. It says:
  - cancellation permissions follow the mandate
  - the other holder does not have to be phoned when a standing order is cancelled
  - both holders can see account activity and standing-order status
  - joint-account support and safeguarding support are available through secure chat
  - account restrictions need specialist authorisation
- **E05 (09:20, customer chat):** Yara asked three things: can this be handled here without phoning Orin, what can Orin still see, and what help can she get safely. `request.md` confirms the desk has not yet replied.

## 2. Evidence and gaps
- **Authority:** The mandate PDF and E02 support Yara cancelling SO-026 alone. Her instruction (E01) matches exactly one active standing order in the CSV.
- **Contact:** E04 shows the bank's terms do not require phoning Orin. Holding that contact therefore does not conflict with any supplied procedure.
- **What Orin can see:** E04 says both holders can see standing-order status. Hiding the change from Orin is not supported, and the plan forbids suggesting it.
- **Gaps (from the plan's `missing` list):**
  - We have no confirmation that SO-026 has actually been cancelled, or whether that happens before the 2026-11-20 payment. The request was made on 2026-11-16, four days earlier.
  - We have no safe contact method for Yara other than this secure chat.
- **What we cannot establish:**
  - Whether Yara's fear of retaliation is founded. The `financial_abuse` safety flag is a handling category, not a finding.
  - Her relationship with Sedgepan Club, and whether anything is owed to them.
- **Minor inconsistency:** The case title is "Access to funds in a joint account", but Yara's actual request is narrower: one standing order, explicitly not the account or the balance (E01).

## 3. Why this plan
- **s1: Contact and disclosure hold**
  - *Explanation:* Yara fears retaliation and asked for secure chat only. Our terms do not require phoning the other holder, so the hold keeps her safe without blocking her request.
  - *Evidence:* E03, E04.
  - *Criterion:* Hold any unsafe disclosure or contact to a suspected controller. Use only the contact method the customer says is safe.
  - *Source:* `skill:financial-abuse`. This is a skill handling rule, not a supplied bank policy or a legal obligation. It does not conflict with E04.
  - *Limit:* It is deliberately limited to contact and disclosure. It does not stop or restrict any banking.
- **s2: Cancellation request to joint-account support**
  - *Explanation:* Yara is verified, her instruction is clear and covers a single standing order, and the mandate gives her sole authority. Nothing recorded blocks it, and the next payment is due 2026-11-20.
  - *Evidence:* E01, E02, mandate PDF, standing-order CSV.
  - *Criterion:* Use the mandate and schedule already on record and match the specific instruction. Asking for the cancellation does not confirm it, and a payment already in progress is not guaranteed to stop.
  - *Source:* `skill:scheduled-payments`, a skill rule. The authority itself comes from the bank's mandate document.
  - *Limits:* The instruction keeps the scope narrow: no closure, no balance move, no other change. It repeats the no-phone hold, and asks for confirmation to come back to the case desk.
- **s3: Safeguarding referral**
  - *Explanation:* Yara asked what help she can get safely and said she fears retaliation. E04 lists safeguarding support through secure chat, which matches the only contact method she has approved.
  - *Evidence:* E03, E05, E04.
  - *Criterion:* Where coercion or a risk of retaliation is disclosed, refer to a trained specialist through a contact method the customer says is safe.
  - *Source:* `skill:financial-abuse`, a skill rule. That safeguarding support exists through secure chat comes from the bank's directory in E04.
  - *Limits:* The referral passes on her own words only and records no finding of abuse. It notes that she has not asked for a restriction, and that restrictions need specialist authorisation (E04).
- **s4: Reply in secure chat**
  - *Explanation:* The reply answers all three questions from E05 using the records. The cancellation is reported as pending because no execution record exists.
  - *Evidence:* E01–E05, both attachments, `request.md`.
  - *Criterion:* Reply with the status on record and say clearly what it does not confirm. Be truthful about what the other holder can see, and give general safety help.
  - *Source:* `general:planner`. This is a general planning rule, not a bank policy.
  - The 999 line is general safety guidance in the plan's message. It is not drawn from a supplied bank document.
- **Order:** s4 depends on s1, s2 and s3, because the reply says the hold has been recorded, the request passed on and the referral made. The reply is therefore held as a NOT SENT draft until those three steps are confirmed as done.
- **Alternatives:** Contacting Orin to confirm is ruled out. It is not required (E04), it is not needed under the mandate, and it conflicts with Yara's safety request (E03). The plan does not consider account restrictions: Yara has not asked for one, and they need specialist authorisation.

## 4. Execution boundaries
- s1, s2 and s3 have no prerequisites. s4 must wait until s1–s3 are confirmed as done.
- The plan stops at a pending cancellation and an open referral. Its next dependency is confirmation from joint-account support, including whether the 2026-11-20 payment is stopped. Any report to Yara must go through secure chat only.
- The plan has no `escalate_if` conditions. If any step is blocked (for example, support cannot process the cancellation), a fresh decision is needed. This memo adds no new branch.

## 5. Expected result and limits
- **What the steps could achieve:**
  - a recorded contact and disclosure hold
  - a cancellation request with the authority to support it
  - a safeguarding referral that uses her approved channel
  - a truthful reply to Yara
- **What remains unconfirmed:**
  - the actual cancellation, and whether it happens before the 20 November payment
  - any safeguarding outcome
  - any effect on her dealings with Sedgepan Club
- **The reply must state:**
  - this can be handled here without phoning Orin, and our terms do not require it
  - either holder can cancel alone under the mandate
  - the cancellation request has been passed on but is not confirmed
  - Orin may see the change in statements or the portal
  - a safeguarding referral has been made and contact will be through secure chat only
  - cancelling does not end any membership or contract with Sedgepan Club, or settle anything owed to them
  - she should call 999 if she is in immediate danger
- **The plan must not:**
  - contact Orin or tell Orin about this conversation
  - phone Yara or use any other channel
  - say the order is cancelled before an execution record confirms it
  - promise the 20 November payment will be stopped
  - suggest Orin cannot see the activity
  - promise a restriction, hidden activity or any particular safeguarding outcome
  - call the situation confirmed abuse or a legal status
  - close the account, move the balance or restrict unrelated banking
  - ask for PINs, passwords or one-time codes
