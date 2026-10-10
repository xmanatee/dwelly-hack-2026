# Supplied case 022

## history.md

# Case 022 history — Available balance after a card purchase

Total events: 5

## 2026-11-10 09:00+00:00 — event 001 (E01)

- **Channel:** Internal card view
- **From:** Brackenfold Bank card ledger
- **To:** Brackenfold Bank case desk

Card and balance entries retrieved at 09:00. The account holder is Rois Fenwick; current contact authentication is recorded as passed.

Attachments: [card-entries.csv](attachments/card-entries.csv)

## 2026-11-10 09:10+00:00 — event 002 (E02)

- **Channel:** Authenticated customer chat
- **From:** Rois Fenwick
- **To:** Brackenfold Bank case desk

The hotel took £600 and £520, so that is £1,120. My available balance is only £380. I thought the stay cost £520.

## 2026-11-10 09:15+00:00 — event 003 (E03)

- **Channel:** Merchant email, bank support copied
- **From:** Alderclock Hotel
- **To:** Rois Fenwick

Your final stay receipt is attached. The stay ended this morning; the final card amount is £520.

Attachments: [hotel-receipt.pdf](attachments/hotel-receipt.pdf)

## 2026-11-10 09:20+00:00 — event 004 (E04)

- **Channel:** Internal procedure view
- **From:** Brackenfold Bank card operations
- **To:** Brackenfold Bank case desk

Card servicing procedure: card operations can investigate a lingering linked authorisation following a completed purchase and release an eligible stale hold after checking linkage and current network state. Case desk may request investigation; it cannot release a hold itself. Release timing depends on those checks.

## 2026-11-10 09:25+00:00 — event 005 (E05)

- **Channel:** Customer chat
- **From:** Rois Fenwick
- **To:** Brackenfold Bank case desk

Can you get the £600 back into my available money today? I need groceries and cannot wait for a generic answer about the hotel.


## request.md

# Case 022: Available balance after a card purchase

## Case details

- **Source role:** Rois Fenwick
- **Status:** Requires decision
- **Created:** 2026-11-10 09:00+00:00
- **Updated:** 2026-11-10 09:25+00:00
- **Operator:** Brackenfold Bank case desk

## Context

An authenticated cardholder asks about hotel entries on account SYN-ACCT-B022 and needs access to available funds today.

## Initial request

Can you get the £600 back into my available money today? I need groceries and cannot wait for a generic answer about the hotel.

## Decision point

No desk response to the final request is recorded. Using the complete history and supplied evidence, recommend the next action, recipient and communication, explaining uncertainty and confidence.

## History

[Read the complete event history](history.md)

## Attachments

- [card-entries.csv](attachments/card-entries.csv)
- [hotel-receipt.pdf](attachments/hotel-receipt.pdf)


## attachments/card-entries.csv

issuer,account,entry_type,reference,linked_authorisation,amount_gbp,status,recorded_at
Brackenfold Bank,SYN-ACCT-B022,opening_ledger,OPEN,,1500.00,booked,2026-11-10T00:00:00+00:00
Brackenfold Bank,SYN-ACCT-B022,card_debit,FINAL-022,AUTH-022,-520.00,booked,2026-11-10T08:30:00+00:00
Brackenfold Bank,SYN-ACCT-B022,authorisation_reservation,AUTH-022,AUTH-022,600.00,active,2026-11-10T09:00:00+00:00
Brackenfold Bank,SYN-ACCT-B022,ledger_balance,BAL,,980.00,snapshot,2026-11-10T09:00:00+00:00
Brackenfold Bank,SYN-ACCT-B022,available_balance,AVL,,380.00,snapshot,2026-11-10T09:00:00+00:00


## attachments/hotel-receipt.pdf

FICTIONAL FACSIMILE · SYNTHETIC EXERCISE
Final stay receipt
Issuer: Alderclock Hotel
Guest: Rois Fenwick
Receipt: SYN-HOTEL-022
Stay: 2026-11-07 to 2026-11-10
Issued: 2026-11-10 09:10+00:00
Final amount paid by card: GBP 520.00
Payment reference: FINAL-022
Authorisation reference: AUTH-022
Synthetic exercise material | Page 1 of 1
