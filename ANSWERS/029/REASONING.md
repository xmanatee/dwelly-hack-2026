# Decision memo for case 029: balance after a payment recovery request

The full input is saved in `context.md`. This memo uses only that context and the plan of record. None of the actions described here has been carried out.

## 1. Situation and history
All events are on 2026-11-19, account SYN-ACCT-B029.

**Bank records (authenticated):**
- **E01, 09:00 (internal ledger view):** opening balance £500, incoming payment £2,000, the customer's own outgoing payment of £600. Booked ledger balance £1,900. Customer contact authentication passed.
- **E02, 09:10 (interbank request record):** Synthetic Sender Bank asked to recover £2,000 on incoming reference IN-029. The request was received and the investigation is pending. The same record says that, under the bank's process, the recovery team makes recovery decisions and reviews holds. The case desk may ask for the current status and a hardship review.
- **E03, 09:15 (internal recovery view):** the recovery team attached `ledger-and-reservations.csv` and `recovery-status.json`.

**Customer's report:**
- **E04, 09:20 (authenticated chat):** she quotes her screen labels, "recovery requested £2,000" and "reserved £1,200". She asks whether the bank took both and notes her available balance is £700.
- **E05, 09:25:** she asks the bank to "restore the £3,200 you took", to confirm the sender has already been repaid, and says she needs money for food. `request.md` repeats this and records no reply from the desk.

The labels she quotes match the bank records. Her reading of them, that £3,200 was taken and the sender was repaid, does not.

## 2. Evidence and gaps
- **No £3,200 debit.** `ledger-and-reservations.csv` shows the following booked entries:
  - OPEN £500.00
  - IN-029 +£2,000.00
  - OUT-029 −£600.00

  That gives a ledger balance of £1,900.00 (500 + 2,000 − 600). The CSV has no recovery debit. HOLD-029 for £1,200.00 is a `recovery_reservation` with status `active`, not a booked entry. Available balance is £700.00 (1,900 − 1,200), which matches E04.
- **No return to the sender.** `recovery-status.json`, retrieved at 09:15, shows:
  - status `request_received`
  - requested £2,000.00
  - reserved £1,200.00
  - booked return £0.00
  - decision `pending`

  E02 agrees.
- **Who decides.** E02 says hold reviews and recovery decisions belong to the recovery team, and that the desk may only ask for status and a hardship review.
- **Hardship.** The only evidence is her own statement in E05 that she needs money for food. Nothing else in the records shows her wider circumstances.

**What we don't know (from the plan's `missing` list, plus points the context leaves unexplained):**
- the recovery team's decision on IN-029, which was pending at 09:15
- the outcome of a hardship review of HOLD-029, which has not yet been requested
- any recovery status recorded after the 09:15 packet. The figures may have changed since then.
- why £1,200 is reserved against a £2,000 request, and the reason for the dispute. The plan forbids guessing at either.

## 3. Why this plan

**s1: decline both requests (`hold_or_decline`)**
- *Explanation:* £1,200 is reserved and £0.00 has been returned on a pending £2,000 request. So the claim that £3,200 was taken and the claim that the sender was repaid are both unsupported.
- *Evidence:* `recovery-status.json`, `ledger-and-reservations.csv`, `history.md`.
- *Criterion:* state only the stage the records prove. A recovery request is not a completed return, and a reservation is not a debit.
- *Source:* skill:payments. This is a handling rule from a skill, not a supplied bank policy or a legal obligation.
- Restoring £3,200 would reverse money that was never debited. Changing the hold is outside the desk's authority under E02. That is why both requests are declined, not partly granted.

**s2: refer to the recovery team for a hardship review (`refer_specialist`)**
- *Explanation:* she reports hardship with essential living costs. Under the bank's process, the case desk may request a hardship review, and decisions on the hold stay with the recovery team.
- *Evidence:* `history.md` (E02, E05) and `ledger-and-reservations.csv`.
- *Criterion:* when essential living costs are affected, refer her to the right support team. The desk uses its stated permission to ask the team that owns hold decisions for a hardship review.
- *Source:* skill:vulnerability-support, which is a skill handling rule. The desk's permission and the recovery team's ownership come from the bank-process statement in E02, which is a supplied record.
- The referral should also ask for the current recovery status, because the latest record is from 09:15. It must not pre-approve any release. The plan flags `financial_difficulty`, and identity is recorded as established (E01, E04).

**s3: reply to the customer (`reply_to_customer`, requires s2)**
- *Explanation:* she needs a clear account of what was reserved and what was requested, the true return status, and the hardship step, with no promised outcome.
- *Evidence:* `recovery-status.json`, `ledger-and-reservations.csv`, `history.md`.
- *Criterion:* reply with the recorded status and say what it does not confirm. Only report the referral as made once the recovery team has confirmed receiving it.
- *Source:* general:evidence.
- The reply comes after s2 so the hardship wording is accurate. The draft in ANSWER.md says the request is being made. The past-tense version is kept as a NOT SENT draft, to be used only once the recovery team confirms it received s2. The MoneyHelper pointer comes from the plan's own instruction, not from a supplied bank policy.

## 4. Execution boundaries
- s1 and s2 do not depend on anything else. s3 depends on s2.
- The plan has no conditional branches and no `escalate_if` triggers.
- The desk stops after the reply. The recovery decision and any change to HOLD-029 are for the recovery team. If any step can't be carried out, for example the referral can't be submitted, that needs a fresh decision. This memo does not propose an alternative.

## 5. Expected result and limits
**What these steps could achieve:**
- the customer gets an accurate explanation of her balance
- her request for a hardship review reaches the team that can decide on the hold
- she hears about free debt advice

**What remains unconfirmed:**
- whether the hold will be released or reduced, and when
- the recovery outcome
- any status change after 09:15

The expected disposition is **escalated**.

**The customer message must say:**
- £3,200 has not been taken. The £2,000 is a recovery request from the sender's bank, not a debit.
- £1,200 is on hold pending the recovery team's decision. It is still in the £1,900 ledger balance, which is why £700 is available.
- £0.00 has been returned and the decision is pending, so the desk cannot confirm the sender has been repaid.
- A hardship review of the hold is requested because she needs money for food, and the outcome is not known. Use "is being requested" until the recovery team confirms receipt, then "has been requested".

**The customer message must not:**
- say £3,200 or £2,000 was debited or taken
- confirm the sender was repaid
- promise the hold will be released, reduced or decided by any time
- predict the recovery outcome or guess at the reason for the dispute
- suggest high-cost borrowing
