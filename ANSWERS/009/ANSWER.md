# Decision

**Hold closure today — pending the customer's informed confirmation (disposition: `needs_info`).**

Owen Price (ID&V passed, event-002) has asked for his Harrow & Vale current account to be closed today with the balance sent to his new bank, and for "anything that comes in" to be forwarded (event-004). The account record (event-001, `attachments/account_summary.csv`) does not match his statement that nothing remains: two active Direct Debits, a standing order and recurring employer credits are still attached, and no CASS switch request is on file. The supplied closure policy permits closure on instruction but requires a failure warning first. The request to manually forward future inbound payments is declined as unsupported — no such facility exists in the supplied policy; only a CASS full switch requested via the new bank redirects payments.

Nothing has been executed. The account is not closed, the £12.40 has not been sent, and no mandates have been cancelled.

# Proposed actions (in order)

1. **s1 — Hold / decline (Servicing agent).** Hold execution of the closure pending the customer's informed confirmation after the mandatory failure warning. Decline the request to manually forward future inbound credits to another bank (no such facility supplied; CASS full switch is the only redirection route).
2. **s2 — Reply to customer (on the call).** Give the recorded status and the required failure warning (script below). Depends on s1.
3. **s3 — Ask customer.** Ask for one decision — close today anyway, or keep open until mandates/CASS are arranged — and record the answer verbatim together with the new-bank sort code and account number nominated for the closing balance. Depends on s2. The plan stops here.

# Message to the customer (proposed — to be said on the call, not yet delivered)

> Before I close it, our record shows these are still attached to this account: a Direct Debit to Meridian Motor Insurance for £68.20 due 1 October, a Direct Debit to FitLife Gyms for £45.00 due 1 October, a standing order of £200 to S PRICE due 28 September, and your employer's expense reimbursements still come here (last one £83.10 on 14 September). There is no switch request on file.
>
> If I close the account today, those Direct Debits and the standing order will fail and any expenses your employer sends here will not reach you — I'm required to warn you of that. The insurer letter you forwarded says a missed payment can lead to your policy being cancelled after 14 days unpaid, so please make sure that Direct Debit is set up at your new bank before 1 October.
>
> I can't set up forwarding of future payments to another bank; the only way to have payments in and out redirected is a full switch through the Current Account Switch Service, which you request from your new bank — it then redirects payments for three years.
>
> Your current balance is £12.40 and it would be paid to the account you nominate when closure is processed. Nothing has been closed yet.
>
> Knowing those items will fail, do you want me to close the account today anyway, or keep it open while you set up the insurance and gym Direct Debits, the standing order to your mum and your employer payments at the new bank (or ask the new bank for a full switch), and then close it? And can you give me the sort code and account number you want the closing balance paid to?

# What is still needed before anything is executed

- The customer's informed choice after the warning (close today regardless / hold until re-pointed or CASS requested).
- The new-bank sort code and account number for the £12.40 closing balance (mentioned on the call, not recorded in evidence).
- Whether replacement DDs/SO already exist at the new bank (H&V records still show the instructions active).
