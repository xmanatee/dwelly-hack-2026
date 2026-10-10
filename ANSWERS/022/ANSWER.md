# Case 022 — Available balance after a card purchase

## Decision

**Escalate to card operations** with a time-sensitive investigation request for the lingering £600 authorisation hold (AUTH-022), and reply to the customer explaining the difference between the booked £520 debit and the active £600 hold. The case desk cannot release the hold itself; release and timing depend on card operations' linkage and network-state checks.

## Proposed actions (in order)

1. **s1 — Request card operations action (proposed, not yet executed)**
   Target: Brackenfold Bank card operations.
   Ask them to investigate the lingering linked authorisation on account SYN-ACCT-B022: AUTH-022, £600.00, status active, recorded 2026-11-10T09:00, linked to booked card debit FINAL-022 (−£520.00, 2026-11-10T08:30). Pass the Alderclock Hotel receipt SYN-HOTEL-022 (issued 2026-11-10 09:10) confirming a final amount of £520.00 with payment reference FINAL-022 and authorisation reference AUTH-022, stay ended 2026-11-10. Ask them to check linkage and current network state and release the hold if eligible under the card servicing procedure (E04). Mark as time-sensitive because the customer states they need the funds today for groceries. Ask for confirmation of outcome and expected timing back to the case desk.

2. **s2 — Reply to the customer via authenticated chat (proposed, after s1 is acknowledged)**
   Target: Rois Fenwick. Message draft below. Because s1 has not yet been acknowledged as sent, the draft uses "I am raising" wording; a post-acknowledgement variant is provided separately.

## Draft message to the customer (pending — not sent)

> I've checked your account. Only £520 has actually been taken — that is the hotel's final charge (reference FINAL-022, booked 08:30 today), and your ledger balance is £980. The £600 you see is not a second charge: it is the authorisation hold the hotel placed when you checked in, which is still showing as active and is linked to the same stay. The hotel has not taken £1,120. While the hold stays active it reduces your available balance to £380.
>
> I am raising a request with our card operations team to check this hold against the completed £520 payment and release it if it qualifies, and I am marking it as urgent because you need the money today. I have to be honest that our desk cannot release the hold directly and the timing depends on card operations' checks, so I can't guarantee it will be back today. I will update you as soon as they respond.
>
> If the delay is leaving you struggling to cover essentials, our financial support team can help — let me know if you'd like that.

## Expected disposition

Escalated — pending card operations' eligibility determination and release timing for AUTH-022.


## Future message draft — NOT SENT

Use only after confirmed execution of: s1.

> I've checked your account. Only £520 has actually been taken — that is the hotel's final charge (reference FINAL-022, booked 08:30 today), and your ledger balance is £980. The £600 you see is not a second charge: it is the authorisation hold the hotel placed when you checked in, which is still showing as active and is linked to the same stay. The hotel has not taken £1,120. While the hold stays active it reduces your available balance to £380. I have raised a request with our card operations team to check this hold against the completed £520 payment and release it if it qualifies, and I have marked it as urgent because you need the money today. I have to be honest that our desk cannot release the hold directly and the timing depends on card operations' checks, so I can't guarantee it will be back today. I will update you as soon as they respond. If the delay is leaving you struggling to cover essentials, our financial support team can help — let me know if you'd like that.
