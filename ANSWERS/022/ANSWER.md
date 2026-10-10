## Decision

**Disposition: escalated to Brackenfold Bank card operations.** Nothing below has been done yet. All actions are proposed and pending.

The records show **one** hotel debit of **£520** (FINAL-022). The **£600** is an active authorisation reservation (AUTH-022), not a second charge. It has the same authorisation reference as the £520 debit and the hotel's final receipt. The case desk cannot release a hold. The proposal is to ask card operations to check AUTH-022 and release it if it is eligible, and to tell the customer the current position without promising when, or whether, the hold will be released.

## Proposed actions (in order)

1. **s1: Request card operations action (pending)**
   - **To:** Brackenfold Bank card operations
   - **Request:** Investigate the lingering authorisation reservation **AUTH-022** (£600.00, active in the 09:00 ledger snapshot) on account **SYN-ACCT-B022**. The cardholder is **Rois Fenwick**, and contact authentication is recorded as passed. Release the hold if it is an eligible stale hold.
   - **Details to pass on:**
     - At 08:30 the ledger booked card debit FINAL-022 for £520.00, linked to AUTH-022.
     - Alderclock Hotel final receipt **SYN-HOTEL-022** says the stay ended on 10 November 2026. It gives a final amount of £520.00, with references FINAL-022 and AUTH-022.
     - At 09:00 the available balance was £380.00 and the ledger balance was £980.00.
   - **Also:** Say that the customer needs the funds for groceries today, and ask them to prioritise the check if their procedure allows. Ask them to confirm they have received the request and to send the outcome to the case desk.

2. **s2: Reply to the customer in authenticated chat (pending; depends on s1)**
   - Use the message below.
   - Until card operations acknowledges s1, the reply must say the request **is being raised**, not that it has been sent. A version for after acknowledgement is drafted separately.

## Message to customer (to use before card operations acknowledges s1)

> Thank you for sending the hotel receipt. Our records show the hotel took one payment of £520 (reference FINAL-022), which matches your final receipt. The £600 is not a second charge. It is a pending authorisation hold with the same authorisation reference (AUTH-022) as the £520 payment and your hotel's final receipt.
>
> As of 09:00, your ledger balance was £980 and your available balance was £380, because the £600 hold is still reserved.
>
> We are raising a request with our card operations team to check this hold and release it if it is eligible. I can't release the hold myself. Card operations has to check it first, and the timing depends on those checks, so I can't promise the money will be back in your available balance today. You can still use the £380 available balance shown at 09:00. We will update you once card operations has finished its checks.

## Future message draft — NOT SENT

Use only after confirmed execution of: s1.

> Thank you for sending the hotel receipt. Our records show the hotel took one payment of £520 (reference FINAL-022), which matches your final receipt. The £600 is not a second charge. It is a pending authorisation hold with the same authorisation reference (AUTH-022) as the £520 payment and your hotel's final receipt. As of 09:00, your ledger balance was £980 and your available balance was £380, because the £600 hold is still reserved. We have asked our card operations team to check this hold and release it if it is eligible. I can't release the hold myself. Card operations has to check it first, and the timing depends on those checks, so I can't promise the money will be back in your available balance today. You can still use the £380 available balance shown at 09:00. We will update you once card operations has finished its checks.
