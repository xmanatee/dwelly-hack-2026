# Decision memo: case 009, request to close a current account

The full input is in the saved `context.md`.

## 1. Situation and history
All events are dated 2026-09-21. No individual times were recorded, and the events follow the order of the conversation.

**Bank records:**
- **event-001** is an internal account view snapshot. It shows:
  - Owen Price has a personal current account with a balance of £12.40.
  - He opened an account at another bank in August and moved his salary there by hand. There is no CASS request on file.
  - The account still has active items attached.
  - The closure policy: an account with active Direct Debits or standing orders can be closed on instruction, but the bank must warn that they will fail. A full CASS switch redirects payments in and out for 3 years and is available within 7 working days of the new bank's request.
- **`attachments/account_summary.csv`** lists the same items:
  - Direct Debit to MERIDIAN MOTOR INSURANCE (policy MMI-44-88120), £68.20, next on 2026-10-01, active
  - Direct Debit to FITLIFE GYMS LTD, £45.00, next on 2026-10-01, active
  - Standing order to S PRICE (ref MUM), £200.00, next on 2026-09-28, active
  - Irregular recurring credits from ELMSTEAD LOGISTICS LTD - EXPENSES, last £83.10 on 2026-09-14
  - Balance £12.40
  - CASS switch request: none on file

**What the customer said:**
- **event-002**: After passing ID&V, he asked to close the account today and send him what is left. He said he had "moved everything" in August.
- **event-004**: He said "there's nothing on it" and asked for anything that comes in later to be forwarded to his new account. He said he was giving the new account details, but they are not in the snapshot.
- **`attachments/insurer_reminder_letter.txt`**: Text he forwarded of a Meridian letter dated 15 Sep 2026. It says that if a monthly payment is not received and is still unpaid after 14 days, the policy will be cancelled, and that driving without insurance is a criminal offence. This is a document he supplied, not a bank record.
- In event-001, the standing order is described as money to his mum. That comes from what he told us, not from a verified record.

**Agent:**
- **event-003**: The agent said "I can arrange that" and asked to check the attached items first. This was not a closure, and no warning was given.

## 2. Evidence and gaps
- **Contradiction.** The customer says nothing is attached (event-002, event-004). The bank records show two active Direct Debits, one active standing order and incoming credits (event-001, account_summary.csv). The records are taken as the true state of the account. His instruction was given on a wrong understanding.
- **Things we can't establish:**
  - Whether he has set up any replacement payment arrangements with Meridian, FitLife or his mother at his new bank. Nothing in the evidence shows this.
  - Whether Meridian or FitLife would accept late payment. Nothing beyond what the letter says is known, and the plan rules out speculating.
- **Missing information (from the plan):**
  1. His informed choice after the warning: close today, or arrange a CASS switch.
  2. The payout account details (name, sort code, account number). He gave them on the call, but they are not in the snapshot. No details are invented here.
  3. A supported H&V way to forward payments by hand to an outside account after closure. None is in the supplied evidence.

## 3. Why this plan
The steps run from identity, to holding the closure, to the warning, to his choice. Each one depends on the step before it, so the account cannot be closed before he has been warned and has confirmed.

- **s1: confirm identity and authority.**
  - Why: event-002 records ID&V passed for the account holder, who is asking to close his own account. Authority is already established.
  - Rule: reuse a verified session and don't add a second identity check.
  - Source: a skill handling rule (`skill:cards-access`), not a bank policy.
- **s2: hold the closure and decline forwarding.**
  - Why: the closure policy in event-001 requires a warning before an account with active Direct Debits or standing orders is closed. His instruction rested on a wrong belief (event-004 against account_summary.csv). The only redirection route in the evidence is CASS, requested by the new bank.
  - Rule: closure on instruction is allowed only after warning that active Direct Debits and standing orders will fail. Don't invent a forwarding procedure that isn't supported.
  - Source: the supplied bank closure policy in event-001.
  - This is a hold, not a refusal. The plan forbids refusing closure outright.
- **s3: warn him on the call.**
  - Why: the records contradict what he believes, and the insurer's letter shows a real risk that his motor policy will be cancelled.
  - Rule: the bank must warn that active Direct Debits and standing orders will fail on closure. Cancelling a payment instruction does not move or pay off the debt behind it.
  - Source: a skill handling rule (`skill:scheduled-payments`). The duty to warn itself comes from the bank policy in event-001.
  - Evidence: event-001, event-004, account_summary.csv, insurer_reminder_letter.txt.
- **s4: ask him to choose and confirm.**
  - Why: closure needs his informed instruction after the warning. The payout details are not in the snapshot, so they must be read back and confirmed.
  - Rule: don't claim closure from a request alone, and confirm the key payout details before acting.
  - Source: a skill handling rule (`skill:cards-access`).
  - Evidence: event-001, event-002, event-004.

The only other option in the evidence is a CASS full switch. It is offered as option (b), and the plan does not add any other strategy. The criminal-offence point is repeated only as the insurer's own wording. It is not presented as legal advice from the bank.

## 4. Execution boundaries
- All four steps are proposed. None has been carried out.
- s3 depends on s2, and s4 depends on s3.
- The plan stops when his choice is recorded at s4. Closing the account, paying out the balance or any CASS action are **not** steps in this plan.
- Once he has confirmed, a new decision will be needed to carry out whichever option he chooses.

## 5. Expected result and limits
**What the steps could achieve:** an informed, recorded choice from the customer and confirmed payout details if he chooses to close.

**What remains unconfirmed:**
- whether he will close or switch
- whether the payout details are correct
- what happens with the third parties (Meridian, FitLife, his mother, his employer)

**What the message must say:**
- the active items, with their amounts and dates
- that the Direct Debits and the standing order will fail if the account closes
- the cancellation warning in Meridian's 15 Sep letter, including the criminal-offence statement
- that H&V cannot forward payments, and CASS is the supported route (3 years, within 7 working days, requested by the new bank)
- that the account has not been closed and his confirmation is needed

**What it must not do:**
- claim the account is closed or the balance paid out
- promise that payments will be forwarded
- claim any payment or credit has been moved to the new bank
- refuse closure outright
- ask for another identity check, or for any PIN, password or one-time code
- speculate about late payment beyond what the letter says
