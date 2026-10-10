---
name: scheduled-payments
description: Standing orders, future payments, Direct Debit mandates, cancellation, amount/date changes and missed collections.
---

# Scheduled Payments

Separate standing order, future one-off payment, Direct Debit and recurring card payment. Match the instruction, next due date and intended change. Cancelling an instruction does not establish that a collected payment was reversed, a debt was cleared or a merchant contract ended.

A mandate marked active does not prove a collection succeeded. A request to change a date or amount is not a confirmed change. Reuse supplied mandate/schedule state and require only missing authorisation or essential parameters. Identify any payment already in flight and avoid promising its cancellation.

External guidance: Pay.UK describes bank/app cancellation and possible in-flight collections. Its Guarantee addresses errors in Direct Debit setup/collection; identify the error and applicable route without promising a refund for every dispute with a supplier. Keep a Guarantee claim separate from changing future instructions.

## Provenance

Reviewed 2026-10-10. UK-oriented guidance; apply only where jurisdiction, event date and scope fit. Case facts and bank procedures must come from supplied evidence.

- [Pay.UK: cancelling a Direct Debit](https://www.directdebit.co.uk/help/cancelling-a-direct-debit/) — UK Direct Debit; not standing orders or card recurring payments.
- [Pay.UK: Direct Debit Guarantee](https://www.directdebit.co.uk/direct-debit-guarantee/) — UK scheme errors; not a universal merchant-dispute refund rule.
