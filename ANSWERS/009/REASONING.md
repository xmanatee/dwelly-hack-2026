# REASONING.md — Case 009, request to close a current account

Full input is saved in `context.md`.

## 1. Situation and history

All events are dated 2026-09-21 (day precision only; conversation order preserved).

- **event-001** (internal account view, authenticated bank record): Owen Price's H&V personal current account, balance £12.40. Customer opened an account at another bank in August and moved his salary **manually**; no Current Account Switch Service request on file. Still attached: DD Meridian Motor Insurance £68.20 (next 1 Oct), DD FitLife Gyms £45.00 (next 1 Oct), SO £200 to "S PRICE" on the 28th monthly, and inbound employer expense reimbursements (last 14 Sep, £83.10). The note also records the closure policy supplied for this case: closure with active DDs/SOs is permitted on instruction but the bank must warn they will fail; a CASS full switch (redirecting payments in and out for 3 years) is available at the new bank's request within 7 working days.
- **event-002** (phone, customer, ID&V passed): asks to close today, says everything moved in August, salary now goes to the new bank, "send me whatever's left".
- **event-003** (phone, agent): says it can be arranged but wants to check items still attached.
- **event-004** (phone, customer): asserts "there's nothing on it", instructs closure, and asks that anything that comes in be forwarded to the new account, "here are the details".
- **`attachments/account_summary.csv`** (bank record): confirms the four items above with policy reference MMI-44-88120, dates 2026-10-01 / 2026-10-01 / 2026-09-28, the £12.40 balance and "CASS switch request: none on file".
- **`attachments/insurer_reminder_letter.txt`** (forwarded by the customer; insurer's text dated 15 Sep 2026): policy MMI-44-88120, £68.20 monthly DD on the 1st; if a payment is not received and remains unpaid after 14 days the policy will be cancelled.

Distinction: the customer's account of having "moved everything" (events 002, 004) is his report. The authenticated record (event-001, `account_summary.csv`) shows active mandates and recurring credits still on the H&V account.

## 2. Evidence and gaps

- **Identity:** ID&V passed on the phone channel (event-002); the plan treats identity authority as established. No safety flags.
- **Contradiction:** the customer says nothing remains (event-004); the bank record shows two active DDs, an active SO and recurring inbound credits with no CASS on file (`account_summary.csv`, event-001). The record is the authoritative source; the customer may have set up duplicate instructions at the new bank, but that cannot be established from the supplied evidence.
- **New-bank details:** event-004 says "here are the details" but no sort code or account number is recorded anywhere in the supplied evidence. They cannot be assumed.
- **Insurer letter:** this is the insurer's stated term, forwarded by the customer. It is not a bank finding and does not establish whether the policy will in fact be cancelled.
- **Forwarding of future credits:** the supplied policy (event-001) describes no facility for H&V to manually forward inbound payments to another bank after closure. The only redirection mechanism supplied is the CASS full switch, requested via the new bank.
- **Not established:** whether the customer already has replacement DDs/SO at the new bank; whether the new bank has been asked for a switch; the customer's decision once warned.

## 3. Why this plan

**s1 — Hold / decline (source: `skill:cards-access`).** The supplied closure policy (event-001) allows closure with active DDs/SOs only after the bank warns the customer they will fail. The customer's instruction in event-004 was given on the mistaken premise that nothing remains, so it is not yet an informed instruction. Criterion: closure permitted only after the failure warning; do not claim closure or invent an unsupported operation from a request alone. The manual forwarding request is declined because nothing in the supplied policy supports it — this is a limit of the supplied bank policy, not a legal finding. The planner notes CASS as the only supplied redirection route. Evidence: event-004, `account_summary.csv`, event-001.

**s2 — Reply to customer (source: `skill:scheduled-payments`).** The customer must be told the recorded status and given the required warning so that his closure instruction can be informed. The script lists exactly the items in `account_summary.csv` (amounts, dates, counterparties), states the consequence of closure (DDs/SO fail, inbound credits not received), relays the insurer's own 14-day term from `insurer_reminder_letter.txt` without asserting what the insurer will do, explains that forwarding is not available and that CASS is requested via the new bank, states the £12.40 balance would be paid to the nominated account only when closure is processed, and says nothing has been closed. Criterion: state the recorded status and what it does not confirm — closing does not establish that payments were re-pointed. Depends on s1 because the warning follows from the decision to hold.

**s3 — Ask customer (source: `general:planner`).** The decisive missing fact is the customer's informed choice after the warning; the second missing input is the nominated account for the closing balance, which is not in evidence. Criterion: request the specific essential missing input and stop; do not schedule closure behind an assumed answer. Depends on s2 — the question only makes sense once the warning has been given.

**Order and alternatives.** The order (hold → warn → ask) follows the supplied policy's sequence: warning before closure. Closing today on the event-004 instruction alone would skip the mandated warning and would, on the record, cause the insurance DD on 1 Oct to fail. Cancelling the DDs/SO proactively is excluded by the plan (`must_not`) because the customer has not instructed it. Setting up forwarding is excluded because no such facility is supplied. The plan does not pre-decide what happens if the customer chooses either option; that is a fresh decision on his answer.

## 4. Execution boundaries

- Nothing has been executed. The account remains open, the £12.40 has not been remitted, no mandates have been cancelled, and no CASS request has been or can be initiated by H&V.
- s2 requires s1; s3 requires s2. Execution stops at s3 pending: (a) the customer's verbatim choice, (b) the new-bank sort code and account number for the closing balance, and (c) whether replacement instructions already exist at the new bank.
- If the customer's answer or the nominated details are not obtained on the call, closure stays held; a new decision is required rather than proceeding on assumption.
- The plan contains no conditional branches and none are added here.

## 5. Expected result and limits

**What the steps can achieve:** an informed closure instruction (or an informed decision to hold), a recorded nomination of the destination account for the balance, and compliance with the supplied warning requirement before any closure. The customer is alerted to the 1 Oct insurance collection and the insurer's stated 14-day cancellation term in time to act.

**What remains unconfirmed:** whether the customer will choose to close today; whether the new bank already holds replacement mandates; whether a CASS switch will be requested, when, or with what outcome (that is the new bank's process, within the supplied "7 working days" availability statement, and H&V cannot promise it); whether the insurer would actually cancel — only the insurer's stated term is relayed.

**Constraints preserved (`must_state` / `must_not`):** the reply states all four attached items with amounts and dates, the failure warning, the insurer's term, the unavailability of manual forwarding and the CASS route, that closure is not yet actioned, and that the £12.40 is paid only when closure is processed. It does not state or imply closure or remittance has happened, does not promise forwarding, does not predict the insurer's decision, does not promise CASS timing or outcome, does not cancel any mandate, and does not request PINs, passwords or one-time codes.
