# REASONING — Case 021: Salary payment P-A after a status-lookup timeout

Full input is in the saved `context.md`. Nothing in this memo has been executed; all actions are proposed.

## 1. Situation and history

Chronology on 2026-11-09 (all UTC):

- **E01, 09:00 — Authenticated bank app record.** Identity/session check passed. Dara Pennick (sole trader, Pennick Loomworks) approved a GBP 2,400 salary instruction, payment ID **P-A**, client reference **SAL-021-A**, destination **SYN-ACCT-EMP021**, from business account **SYN-ACCT-B021** (account per `request.md`). The same record states the service access model: the case desk has enquiry (read-only) access; **payment operations maintains execution records indexed by payment ID**.
- **E02, 09:00:05 — Internal gateway record**, attachment `attachments/gateway-log.json`. Events: `submission` → `accepted` at 09:00:01; `status_lookup` → `timeout` at 09:00:05. `terminal_execution_status` is `null`.
- **E03, 09:05 — Authenticated customer chat.** Customer copies the app wording "Connection timed out while retrieving payment status", says the employee needs the salary today, and asks whether it failed.
- **E04, 09:06 — Internal account view**, attachment `attachments/balance-view.csv`. Snapshot at 09:06:00: ledger GBP 5,000.00, reservation **P-A** GBP 2,400.00, available GBP 2,600.00. Reconciliation state for P-A: **Pending**.
- **E05, 09:07 — Customer chat.** Customer asks to send GBP 2,400 again now under fresh reference **SAL-021-B** to the same destination. This is also the "initial request" in `request.md`. No desk response is recorded.

Distinguishing sources: E01, E02 and E04 are authenticated/internal bank records. E03 and E05 are the customer's own report and request. The customer's reading of the timeout as a possible failure is not corroborated by any bank record; the bank records show acceptance plus an unresolved status.

## 2. Evidence and gaps

**What the records prove**
- P-A was **authorised** by the customer in an authenticated session (E01).
- P-A was **accepted for submission** by the gateway at 09:00:01 (`gateway-log.json`).
- The only recorded "failure" is of the **status lookup**, not of the payment (`gateway-log.json`, E02).
- Funds are **reserved** (GBP 2,400 against P-A) and reconciliation is **Pending** as of 09:06 (`balance-view.csv`, E04). Available balance is GBP 2,600, which is consistent with the reservation still being held.

**What the records do not prove**
- Whether P-A was released/sent to the recipient bank, settled, failed, or returned — `terminal_execution_status` is `null` and no later gateway event is supplied.
- Whether SYN-ACCT-EMP021 has been credited.
- Whether or when the P-A reservation would be released if P-A is confirmed failed.

**Gaps and minor uncertainties (from the plan's `missing` list)**
- Terminal execution status of P-A is the single material gap; it is held by payment operations (E01).
- No `decision_time` is supplied; the latest observation is the 09:06 snapshot, so the state may have moved since.
- E05 is labelled "Customer chat" without the explicit "Authenticated" marker used on E03. It continues the chat opened at 09:05 and the plan treats identity as established; this is noted but does not change the decision, since the plan declines the requested action rather than acting on it.
- No supplied bank policy or payment-scheme commitment specifies arrival times, resend rules or reservation-release timing; the memo cites none.

No contradictions exist between the records. The customer's framing ("so it goes through cleanly") assumes the first payment did not go through, which the records neither confirm nor deny.

## 3. Why this plan

**s1 — hold/decline the resend (case desk).**
Explanation: the payment lifecycle must be read stage by stage — authorisation (proven, E01), submission accepted (proven, gateway log), release/sent and settlement (not proven, terminal status null, reconciliation Pending). An unresolved status is not a failure. Because the original instruction may still execute and the GBP 2,400 remains reserved, a second GBP 2,400 instruction to the same destination risks a duplicate salary. Evidence: `gateway-log.json`, `balance-view.csv`, `history.md`. Criterion: state only the stage the record proves; do not treat an unresolved status as a failure or a resend as safe. Source: the payments handling skill (a desk handling rule, not a supplied bank policy or legal obligation). The case desk's read-only access (E01, `request.md`) also means it could not itself submit a payment, which reinforces that the correct desk action is a hold rather than execution.

**s2 — request team action from payment operations (requires s1).**
Explanation: the null terminal status cannot be resolved with the case desk's enquiry access; E01 names payment operations as the holder of execution records indexed by payment ID. One targeted lookup on P-A closes the material gap, and the request includes the identifiers needed (payment ID, client reference, amount, accounts, gateway timestamps) plus the two questions whose answers determine any later step: terminal status with timestamp, and reservation release if failed/returned. The time-sensitivity is flagged as context, not as a deadline the plan commits to. Evidence: `history.md`, `gateway-log.json`, `balance-view.csv`. Criterion: request a named record lookup only for a material gap, from the team named in the context. Source: payments skill. Ordering: s2 follows s1 so that the hold is in place before any upstream enquiry, ensuring no payment is submitted while the lookup is pending.

**s3 — reply to the customer in the authenticated chat (requires s1 and s2).**
Explanation: the customer asked a direct question ("Did it fail?") and made a direct request (resend). The reply answers with the proven stage (accepted 09:00:01; GBP 2,400 reserved; reconciliation Pending; no final status), explains the duplicate risk as the reason for the hold, and reports the payment-operations lookup as pending. It expressly does not promise an arrival time, because no applicable commitment is in the supplied evidence. Evidence: `history.md`, both attachments, the request. Criterion: reply with the recorded status and what it does not confirm; no arrival-time promises absent an applicable commitment. Source: payments skill. Ordering: s3 follows s2 because the message tells the customer the lookup is under way; the plan's verbatim wording ("We have asked…") is therefore supplied as a NOT SENT draft gated on s1 and s2, and the answer carries a present-state equivalent.

**Alternatives considered within the plan's grounds.** Submitting SAL-021-B as asked would be supported only by a record proving P-A failed or was returned; no such record exists, so it is not supported. Telling the customer the payment succeeded is equally unsupported. The plan's hold-and-verify course is the only one consistent with the evidence. No additional strategy is added here.

## 4. Execution boundaries

- **s1** has no dependencies and is the immediate safeguard: no new payment instruction is to be created.
- **s2** depends on s1 and is a request to payment operations; its result is unknown until they respond. The plan sets no response deadline and the customer must not be given one.
- **s3** depends on s1 and s2. If s2 cannot be actioned (e.g., the request is blocked), s3's wording about the lookup would be inaccurate and a fresh decision is needed rather than an improvised message.
- The plan **stops after s3**. It deliberately does not pre-decide what happens when payment operations responds: whether to resend if P-A is confirmed failed, whether the reservation is released, or how to confirm credit if P-A is settled. Each of those requires the new information and a new decision. No `escalate_if` conditions and no safety flags are set; identity authority is established.

## 5. Expected result and limits

**What the proposed steps could achieve:** prevent a duplicate GBP 2,400 salary payment; obtain the authoritative terminal status of P-A from the team that holds it; give the customer an accurate account of the recorded stage and the reason for the hold, with a commitment to update in the same chat.

**What remains unconfirmed:** whether P-A has been sent, settled, failed or returned; whether the employee has been or will be credited today; whether and when the GBP 2,400 reservation will be released. The customer's need for same-day payment is acknowledged but cannot be guaranteed from current records.

**Constraints carried into the message (plan `must_state` / `must_not`):** the reply must say that a status-lookup timeout is not a failure record, that P-A was accepted at 09:00:01 with no final status yet, that GBP 2,400 is reserved with reconciliation Pending, that the resend is held because of duplicate risk, that payment operations is being asked to confirm, and that credit/arrival today cannot be confirmed. It must not say P-A failed, was returned or was delivered; must not submit or promise SAL-021-B; must not promise an arrival time or same-day receipt; must not give a response time for payment operations; and must not describe the lookup as completed or its result as known.

**Confidence:** high that the hold is correct on the current evidence; the outcome for the employee's salary is genuinely undetermined until payment operations confirms.
