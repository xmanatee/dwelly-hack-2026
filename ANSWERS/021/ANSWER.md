# Case 021: Salary payment P-A after a connection timeout

## Decision
**Put the requested second GBP 2,400 payment (SAL-021-B) on hold and pass the case to Payment operations.** Expected outcome: **escalated**.

Our records do not show that payment P-A (GBP 2,400, reference SAL-021-A, to SYN-ACCT-EMP021) failed:
- The gateway accepted it at 09:00:01.
- The only timeout was a status lookup at 09:00:05.
- GBP 2,400 is still reserved against P-A.
- Reconciliation is Pending, and no final execution status has been recorded.

If we send a second payment now, the employee could be paid twice. The case desk also has enquiry access only.

## Proposed actions (in order, none carried out yet)
1. **s1: Hold the second payment.** Do not submit or arrange the GBP 2,400 payment with reference SAL-021-B. Keep the hold until Payment operations reports P-A's final status.
2. **s2: Ask Payment operations to check the record.** Ask them to review the execution record for payment ID P-A and send its final status (executed/sent, rejected or failed) back to the case desk. Include these details:
   - Account SYN-ACCT-B021, Pennick Loomworks, sole trader Dara Pennick (authenticated)
   - Payment P-A, client reference SAL-021-A, GBP 2,400.00, destination SYN-ACCT-EMP021
   - The gateway accepted the submission on 2026-11-09 at 09:00:01. The status lookup timed out at 09:00:05. terminal_execution_status is null.
   - The ledger at 09:06 shows a GBP 2,400 reservation under P-A, and reconciliation is Pending.
   - The customer asked for a resend under SAL-021-B. It is on hold to avoid a duplicate. The customer says the salary is needed today.
3. **s3: Reply to the customer.** Send this only after s1 and s2. The wording below assumes s2 has not been acknowledged yet.

## Message to the customer (draft, not sent)
> Thank you for sending the exact message. It means the app couldn't get the payment status, not that the payment failed. Our records show salary payment P-A (GBP 2,400, reference SAL-021-A) was accepted when submitted at 09:00. GBP 2,400 is currently reserved on your account against it, and it is still pending, with no final result recorded yet. Because of that, we are not sending a second GBP 2,400 under SAL-021-B now. If the original payment also goes through, your employee would be paid twice. We are asking our Payment operations team to check the execution record for P-A and confirm its final status. That result is still pending. We'll update you once they confirm it. We can't confirm yet whether or when the funds will reach your employee.

*Use the "We have asked…" version only after Payment operations acknowledges the s2 request. That version is held separately as a future message.*


## Future message draft — NOT SENT

Use only after confirmed execution of: s1, s2.

> Thank you for sending the exact message. It means the app couldn't get the payment status, not that the payment failed. Our records show salary payment P-A (GBP 2,400, reference SAL-021-A) was accepted when submitted at 09:00. GBP 2,400 is currently reserved on your account against it, and it is still pending, with no final result recorded yet. Because of that, we are not sending a second GBP 2,400 under SAL-021-B now. If the original payment also goes through, your employee would be paid twice. We have asked our Payment operations team to check the execution record for P-A and confirm its final status. That result is still pending. We'll update you with the result once they confirm it. We can't confirm yet whether or when the funds will reach your employee.
