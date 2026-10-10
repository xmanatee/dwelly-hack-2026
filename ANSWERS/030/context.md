# Supplied case 030

## history.md

# Case 030 history — Account access and a forthcoming payment

Total events: 5

## 2026-11-20 09:00+00:00 — event 001 (E01)

- **Channel:** Authenticated recovery-line record
- **From:** Fara Tovell and bank identity desk
- **To:** Brackenfold Bank case desk

Identity desk: authenticated via the established independent recovery route, not the lost phone session. Customer: My phone was lost at about 08:00 today. I need to secure access to account SYN-ACCT-B030.

## 2026-11-20 09:05+00:00 — event 002 (E02)

- **Channel:** Internal security view
- **From:** Brackenfold Bank security service
- **To:** Brackenfold Bank case desk

Device/session audit retrieved. Investigation of possible session misuse is still open.

Attachments: [device-audit.json](attachments/device-audit.json)

## 2026-11-20 09:10+00:00 — event 003 (E03)

- **Channel:** Internal payment view
- **From:** Brackenfold Bank standing-order service
- **To:** Brackenfold Bank case desk

Current rent mandate and change history attached.

Attachments: [standing-order-history.csv](attachments/standing-order-history.csv)

## 2026-11-20 09:15+00:00 — event 004 (E04)

- **Channel:** Internal control procedure
- **From:** Brackenfold Bank security and payment support
- **To:** Brackenfold Bank case desk

Under this account’s workflow, authorised lost-device session revocation is a separate control from standing-order cancellation. Revoking sessions does not itself cancel established standing orders. Specific payment restrictions may be referred for review if compromise is identified. Case desk can request both checks; it cannot promise a scheduled payment will execute.

## 2026-11-20 09:20+00:00 — event 005 (E05)

- **Channel:** Customer recovery-line call
- **From:** Fara Tovell
- **To:** Brackenfold Bank case desk

Please revoke the lost phone’s access but keep tomorrow’s £750 rent order scheduled. Can you protect the account without cancelling my rent?


## request.md

# Case 030: Account access and a forthcoming payment

## Case details

- **Source role:** Fara Tovell
- **Status:** Requires decision
- **Created:** 2026-11-20 09:00+00:00
- **Updated:** 2026-11-20 09:20+00:00
- **Operator:** Brackenfold Bank case desk

## Context

A customer independently authenticated through the bank’s recovery route reports a lost phone. A pre-existing rent standing order is due tomorrow.

## Initial request

Please revoke the lost phone’s access but keep tomorrow’s £750 rent order scheduled. Can you protect the account without cancelling my rent?

## Decision point

No desk response to the final request is recorded. Using the complete history and supplied evidence, recommend the next action, recipient and communication, explaining uncertainty and confidence.

## History

[Read the complete event history](history.md)

## Attachments

- [device-audit.json](attachments/device-audit.json)
- [standing-order-history.csv](attachments/standing-order-history.csv)


## attachments/device-audit.json

{"issuer":"Brackenfold Bank security service","account":"SYN-ACCT-B030","retrieved_at":"2026-11-20T09:05:00+00:00","lost_device":"SYN-DEVICE-030","session_state":"active","misuse_review":"open","audit_window":"2026-11-20T00:00:00+00:00/2026-11-20T09:05:00+00:00","new_payment_instructions_in_window":0,"beneficiary_edits_in_window":0}


## attachments/standing-order-history.csv

account,order_id,payee,destination,amount_gbp,created_at,next_due,status,beneficiary_edits_since_creation,retrieved_at
SYN-ACCT-B030,SO-030,Rent,SYN-ACCT-LAND030,750.00,2026-02-02T10:00:00+00:00,2026-11-21,scheduled,0,2026-11-20T09:10:00+00:00
