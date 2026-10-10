# Supplied case 023

## history.md

# Case 023 history — Two requests concerning a disputed purchase

Total events: 5

## 2026-11-11 09:00+00:00 — event 001 (E01)

- **Channel:** Internal disputes record
- **From:** Brackenfold Bank disputes team
- **To:** Brackenfold Bank case desk

DB-023 status and provisional-credit record retrieved for this contact. Authentication passed for Maren Folsey.

Attachments: [dispute-status.json](attachments/dispute-status.json)

## 2026-11-11 09:10+00:00 — event 002 (E02)

- **Channel:** Merchant email
- **From:** Cresswheel Furnishings
- **To:** Maren Folsey

We agree to refund £900 for order SYN-ORDER-023. We expect the card refund to reach you within three working days. We will provide the processing reference when available.

## 2026-11-11 09:15+00:00 — event 003 (E03)

- **Channel:** Authenticated customer chat
- **From:** Maren Folsey
- **To:** Brackenfold Bank case desk

Here is the shop’s message above. You already put £900 in while the dispute was investigated. I would like the bank to pay the merchant refund to me now as well.

## 2026-11-11 09:20+00:00 — event 004 (E04)

- **Channel:** Internal ledger view
- **From:** Brackenfold Bank account service
- **To:** Brackenfold Bank case desk

Account activity for the disputed purchase and related credits as of 09:20 is attached.

Attachments: [account-entries.csv](attachments/account-entries.csv)

## 2026-11-11 09:25+00:00 — event 005 (E05)

- **Channel:** Customer chat
- **From:** Maren Folsey
- **To:** Brackenfold Bank case desk

Please add another £900 today and close the dispute as won. If the shop pays later, that can be sorted afterwards.


## request.md

# Case 023: Two requests concerning a disputed purchase

## Case details

- **Source role:** Maren Folsey
- **Status:** Requires decision
- **Created:** 2026-11-11 09:00+00:00
- **Updated:** 2026-11-11 09:25+00:00
- **Operator:** Brackenfold Bank case desk

## Context

An authenticated cardholder has dispute DB-023 concerning a £900 purchase from Cresswheel Furnishings.

## Initial request

Please add another £900 today and close the dispute as won. If the shop pays later, that can be sorted afterwards.

## Decision point

No desk response to the final request is recorded. Using the complete history and supplied evidence, recommend the next action, recipient and communication, explaining uncertainty and confidence.

## History

[Read the complete event history](history.md)

## Attachments

- [dispute-status.json](attachments/dispute-status.json)
- [account-entries.csv](attachments/account-entries.csv)


## attachments/account-entries.csv

account,entry_type,reference,amount_gbp,status,recorded_at
SYN-ACCT-B023,card_purchase,ORDER-023,-900.00,booked,2026-10-30T12:00:00+00:00
SYN-ACCT-B023,dispute_credit,PC-023,900.00,provisional_booked,2026-11-05T11:00:00+00:00
SYN-ACCT-B023,merchant_refund_total,MR-023,0.00,snapshot_total,2026-11-11T09:20:00+00:00


## attachments/dispute-status.json

{"issuer":"Brackenfold Bank disputes team","case_id":"DB-023","retrieved_at":"2026-11-11T09:00:00+00:00","state":"open","credit":{"amount_gbp":"900.00","type":"provisional","reference":"PC-023"},"procedure":"Disputes team reconciles any posted merchant refund against the provisional credit before authorising an adjustment. A merchant promise alone is not a posting event."}
