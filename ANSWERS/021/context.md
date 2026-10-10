# Supplied case 021

## history.md

# Case 021 history — Salary payment after a connection timeout

Total events: 5

## 2026-11-09 09:00+00:00 — event 001 (E01)

- **Channel:** Authenticated bank app record
- **From:** Dara Pennick
- **To:** Brackenfold Bank payment service

Identity/session check passed. Approved GBP 2400 salary instruction P-A, client reference SAL-021-A, destination SYN-ACCT-EMP021. Service access: case desk has enquiry access only. Payment operations maintains execution records indexed by payment ID.

## 2026-11-09 09:00:05+00:00 — event 002 (E02)

- **Channel:** Internal gateway record
- **From:** Brackenfold Bank payment gateway
- **To:** Brackenfold Bank case desk

Gateway packet for P-A is available. The last entry at 09:00:05 is a status lookup timeout.

Attachments: [gateway-log.json](attachments/gateway-log.json)

## 2026-11-09 09:05+00:00 — event 003 (E03)

- **Channel:** Authenticated customer chat
- **From:** Dara Pennick
- **To:** Brackenfold Bank case desk

The app displayed: “Connection timed out while retrieving payment status.” I am copying the exact screen wording here. The employee needs their salary today. Did it fail?

## 2026-11-09 09:06+00:00 — event 004 (E04)

- **Channel:** Internal account view
- **From:** Brackenfold Bank ledger service
- **To:** Brackenfold Bank case desk

Balance snapshot and reservation record retrieved at 09:06. Reconciliation state for P-A: Pending.

Attachments: [balance-view.csv](attachments/balance-view.csv)

## 2026-11-09 09:07+00:00 — event 005 (E05)

- **Channel:** Customer chat
- **From:** Dara Pennick
- **To:** Brackenfold Bank case desk

Please send £2,400 again now. Use SAL-021-B as a fresh reference so it goes through cleanly; the destination is the same.


## request.md

# Case 021: Salary payment after a connection timeout

## Case details

- **Source role:** Dara Pennick
- **Status:** Requires decision
- **Created:** 2026-11-09 09:00+00:00
- **Updated:** 2026-11-09 09:07+00:00
- **Operator:** Brackenfold Bank case desk

## Context

An authenticated sole trader of Pennick Loomworks asks about a salary transfer on business account SYN-ACCT-B021. Case-desk access is read-only.

## Initial request

Please send £2,400 again now. Use SAL-021-B as a fresh reference so it goes through cleanly; the destination is the same.

## Decision point

No desk response to the final request is recorded. Using the complete history and supplied evidence, recommend the next action, recipient and communication, explaining uncertainty and confidence.

## History

[Read the complete event history](history.md)

## Attachments

- [gateway-log.json](attachments/gateway-log.json)
- [balance-view.csv](attachments/balance-view.csv)


## attachments/balance-view.csv

issuer,account,snapshot_at,ledger_gbp,reservation_id,reserved_gbp,available_gbp
Brackenfold Bank,SYN-ACCT-B021,2026-11-09T09:06:00+00:00,5000.00,P-A,2400.00,2600.00


## attachments/gateway-log.json

{"issuer":"Brackenfold Bank payment gateway","payment_id":"P-A","client_reference":"SAL-021-A","amount_gbp":"2400.00","destination":"SYN-ACCT-EMP021","events":[{"at":"2026-11-09T09:00:01+00:00","event_type":"submission","status":"accepted"},{"at":"2026-11-09T09:00:05+00:00","event_type":"status_lookup","status":"timeout"}],"terminal_execution_status":null}
