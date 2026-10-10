# Case 021 — Salary payment P-A after a status-lookup timeout

## Decision

**Hold the resend request. Do not submit a second GBP 2,400 payment (SAL-021-B).** Disposition: **needs_info** — the terminal execution status of payment P-A must be confirmed by payment operations before any further payment decision is taken.

The gateway record shows P-A (client reference SAL-021-A, GBP 2,400.00, SYN-ACCT-B021 → SYN-ACCT-EMP021) was **accepted at 09:00:01**; only the subsequent **status lookup timed out at 09:00:05**, and `terminal_execution_status` is `null`. The 09:06 ledger snapshot still holds a **GBP 2,400 reservation for P-A** with reconciliation **Pending**. The payment is therefore neither proven failed nor proven executed. A second submission now could pay the employee twice.

## Proposed actions (in order — none executed yet)

1. **s1 — Hold / decline the resend (case desk).** Hold the request to send GBP 2,400 with reference SAL-021-B to SYN-ACCT-EMP021. Submit no new payment instruction. Grounds: P-A accepted by the gateway at 09:00:01, terminal status null, GBP 2,400 still reserved, reconciliation Pending → duplicate-salary risk.
2. **s2 — Request team action from Brackenfold Bank payment operations** (depends on s1). Ask payment operations to retrieve the execution record for payment ID **P-A** (client reference SAL-021-A, GBP 2,400.00, debit account SYN-ACCT-B021, destination SYN-ACCT-EMP021, gateway submission accepted 2026-11-09 09:00:01+00:00, status lookup timeout 09:00:05) and confirm to the case desk: (a) the terminal execution status (sent/settled, failed, or returned) with timestamp; (b) if failed/returned, whether the GBP 2,400 reservation P-A has been or will be released. Flag that the customer is asking to resend and that the salary is time-sensitive.
3. **s3 — Reply to Dara Pennick in the authenticated chat** (depends on s1 and s2). Send the message below once the hold and the payment-operations request have been actioned.

## Proposed customer message (pending — not sent)

> Thank you for copying the exact wording. The message "Connection timed out while retrieving payment status" means the app could not retrieve the status; it is not a record that the payment failed. Our gateway shows your GBP 2,400 salary payment P-A (reference SAL-021-A) was accepted at 09:00:01 today, and GBP 2,400 is currently reserved against it on your business account with the reconciliation still pending. No final execution status is recorded yet, so we cannot confirm whether your employee has been credited. Because the original payment may still complete, we are not submitting a second GBP 2,400 payment (SAL-021-B) at this stage, as that could pay your employee twice. We are asking our payment operations team to confirm the final status of P-A from their execution record and will update you in this chat as soon as we have their confirmation. We cannot promise an arrival time for the salary from the current records.

Note: the plan's exact wording ("We have asked our payment operations team…") presumes step s2 has been actioned; that verbatim version is provided separately as a NOT SENT draft to be used once s1 and s2 are acknowledged.

## What the message must and must not say

- Must state: timeout ≠ failure; P-A accepted at 09:00:01 with no final status yet; GBP 2,400 reserved, reconciliation Pending; resend held because of duplicate risk; payment operations lookup requested and an update will follow; the bank cannot confirm the employee has been credited or that funds arrive today.
- Must not: say P-A failed, was returned, or was delivered; submit or promise SAL-021-B; promise an arrival time or same-day receipt; give a response time for payment operations; describe the payment-operations request as completed or its result as known.

## Stop point

The plan stops after s3. Any further step (release of the reservation, a resend, or confirmation of credit) requires payment operations' confirmation and a fresh decision.

## Future message draft — NOT SENT

Use only after confirmed execution of: s1, s2.

> Thank you for copying the exact wording. The message 'Connection timed out while retrieving payment status' means the app could not retrieve the status; it is not a record that the payment failed. Our gateway shows your GBP 2,400 salary payment P-A (reference SAL-021-A) was accepted at 09:00:01 today, and GBP 2,400 is currently reserved against it on your business account with the reconciliation still pending. No final execution status is recorded yet, so we cannot confirm whether your employee has been credited. Because the original payment may still complete, we are not submitting a second GBP 2,400 payment (SAL-021-B) at this stage, as that could pay your employee twice. We have asked our payment operations team to confirm the final status of P-A from their execution record and will update you in this chat as soon as we have their confirmation. We cannot promise an arrival time for the salary from the current records.
