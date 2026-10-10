# Decision memo: Case 006, unexpected £750 credit and redirection request

The full input is saved in `context.md`. This memo explains the plan of record. It does not change it. All actions are **proposed and not yet carried out**.

## 1. Situation and history

**Bank records (authenticated)**
- **26 Sep 2026, 22:14 (a Saturday):** A £750.00 Faster Payment from "R JAMES" at Meridian Bank (SYN-SC-06-2 / SYN-ACCT-06-2) was paid into Aisha Khan's student current account. Reference "RENT", end-to-end ID MER26092622143198. Source: `attachments/inbound_payment_message.json`, event-001.
- In the same payment record, `recovery_request_received` is `false`. Event-001 separately says no funds-recovery request has been received from Meridian.

**What the customer forwarded**
- **27 Sep:** A text from an unknown mobile number. The OCR timestamp is "Sun 27 Sep, 08:41". The case-record transcription (event-001) says "Ryan" asks for the £750 to be sent to "my other account": **SYN-SC-06-3 / SYN-ACCT-06-1, R James**.

**Check carried out in the case record**
- **28 Sep, 09:52:40Z:** A CoP check on SYN-SC-06-3 / SYN-ACCT-06-1 with the name "R James" returned `matched: false`, code **ANNM** (account name does not match). Source: `attachments/cop_check_text_details.json`, event-001.

**The chat on 28 Sep (what the customer says)**
- Event-002: she asks whether she can just send the money back now. She says she hasn't touched it.
- Event-003: the agent says they will look into it.
- Event-004: she points out that the texter gave her a different account from the one the money came from, asks if that is a problem, and says "I just want it gone".

The customer's account of events (her intent, and that she hasn't touched the funds) comes from her own messages. The payment details and the CoP result come from bank records.

## 2. Evidence and gaps

- **Conflicting account details in the text.** Event-001 transcribes the text with SYN-SC-06-3 / SYN-ACCT-06-1. The local machine OCR (`attachments/sms_screenshot.png.ocr.txt`) reads **SYN-SC-06-2 / SYN-ACCT-06-2**, which are the payer's own details. The wording also differs: the OCR has no "Really appreciate it, I'm in a bind". The original image (`attachments/sms_screenshot.png`) was not read. The two sources cannot be reconciled from the material supplied. The plan does not treat either as settled. It asks the fraud team to check the original image.
- **What the CoP result covers.** The CoP check was run only on the details in the case record. If the original image turns out to show the payer's own details, the CoP mismatch would not relate to the text as it actually reads. This is a real limitation. It is one reason the plan hands the decision to fraud specialists instead of drawing a firm conclusion. Even so, the customer herself says (event-004) that the texter gave a different account from the one the money came from. That supports the warning sign independently of the CoP result.
- **Sender's number.** The number +44 7700 900 823 appears only in the OCR. Step s2 passes it on as "per the OCR". It is not confirmed by the case record.
- **Recovery request.** None has been received. Whether Meridian will ever raise one is unknown.
- **What cannot be established:** who sent the text, whether the credit is a genuine mistake, and whether the funds are linked to fraud.

## 3. Why this plan

- **s1: hold the outgoing payment.** The customer intends to send the money now (events 002 and 004). The plan sees concrete warning signs:
  - the destination she was given differs from the paying account
  - that destination failed CoP
  - no recovery request has come from Meridian

  Criterion: *suspected active scam, so hold the risky action and do not help with another transfer.* Source: the **skill:fraud-takeover** handling rule. This is a skill rule, not a supplied bank policy or a cited legal obligation. The plan also tells her not to pay it back to the payer herself. The safe route for returning it is the inter-bank recovery process. The hold is limited to this one payment.
- **s2: urgent fraud referral.** The redirection request and the CoP mismatch suggest a scam attempt may be under way. The inbound credit itself may also need fraud review. How the funds are handled is for fraud specialists to decide, not the servicing agent. Criterion: *escalate urgently and name unresolved conflicting records.* Source: **skill:fraud-takeover**. That is why the OCR/case-record conflict is listed explicitly in the referral.
- **s3: customer reply.** The reply answers her question directly, explains the safe return route, and states what has and has not happened, without promising an outcome. Criterion: *reply with the recorded status and say what it does not confirm. A recall or return request is not a completed return.* Source: **skill:payments**. The reply depends on s1 (`requires: ["s1"]`). The plan also says the referral may only be described as made once s2 is acknowledged. Until then, the reply says it is being arranged.

**Order of steps.** The risky payment is stopped first (s1), then the fraud team is engaged (s2), then the customer is told. No identity check is needed (`identity_authority: not_needed`). Safety flag: `scam_in_progress`.

## 4. Execution boundaries

- None of the steps has been carried out. s3 must not be sent before s1, and the referral wording must stay "being arranged" until s2 is acknowledged.
- After the referral, the plan stops. Checking the original image, deciding how the funds are handled, and any contact with Meridian are all left to the fraud team under bank procedure. `escalate_if` is empty and no conditional branches are defined. If a step cannot be carried out, a fresh decision is needed.

## 5. Expected result and limits

**What the plan could achieve**
- The customer is stopped from sending £750 to a possibly fraudulent account.
- She understands the safe return route.
- Fraud specialists receive the case with the conflicting records flagged.

**What remains unconfirmed**
- Whether the payment was a genuine mistake.
- Which account details the text actually contains.
- Whether Meridian will raise a recovery request.
- How and when the funds will be dealt with.

**What the customer message must include (`must_state`)**
- It is a problem, and asking for a mistaken payment to go to a different account is a common warning sign.
- The name check found the account is not in the name "R James".
- She should not send the money anywhere herself, including back to the payer, and should leave the £750 untouched.
- The sender should go through Meridian, which can ask for the money back through the banks' recovery process. No such request has been received yet.
- The case is being referred to the fraud team, who will contact her through secure channels.
- She should not reply to the texter, and the bank will never ask for her PIN, password or one-time codes.

**What it must not do (`must_not`)**
- Call the texter definitely a scammer, or the money definitely criminal proceeds.
- Say the funds have been frozen, returned or recovered, or that a recovery request has been received.
- Promise a timeframe or outcome.
- Reveal the name actually held on the account checked with CoP.
- Ask for credentials.
- Encourage any outgoing payment of the £750.
- Present either set of account details as settled.
