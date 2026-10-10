# Supplied case 028

## history.md

# Case 028 history — Amount received on an international payment

Total events: 5

## 2026-11-18 09:00+00:00 — event 001 (E01)

- **Channel:** Authenticated portal instruction
- **From:** Perrin Wessel
- **To:** Brackenfold Bank international payments

Identity check passed. Principal: £1,000. Separate sending-bank fee: £5. Selected charge option: Shared. Displayed estimate: EUR1,160 at indicative 1.1600 EUR/GBP; non-binding until execution. Possible intermediary/receiving-bank charges disclosed; customer confirmed the instruction.

## 2026-11-18 09:10+00:00 — event 002 (E02)

- **Channel:** Internal execution view
- **From:** Brackenfold Bank international payments
- **To:** Brackenfold Bank case desk

Execution advice for INT-028 is attached.

Attachments: [execution-advice.pdf](attachments/execution-advice.pdf)

## 2026-11-18 10:00+00:00 — event 003 (E03)

- **Channel:** Recipient email forwarded with provenance
- **From:** Recipient Osa Melwick
- **To:** Perrin Wessel

This is the advice my bank supplied for the payment received this morning.

Attachments: [recipient-advice.pdf](attachments/recipient-advice.pdf)

## 2026-11-18 10:10+00:00 — event 004 (E04)

- **Channel:** Authenticated customer chat
- **From:** Perrin Wessel
- **To:** Brackenfold Bank case desk

The recipient got EUR1,135, not the EUR1,160 I saw. I think EUR25 went missing. The advice is above; please check it.

## 2026-11-18 10:15+00:00 — event 005 (E05)

- **Channel:** Customer chat
- **From:** Perrin Wessel
- **To:** Brackenfold Bank case desk

Please compensate the EUR25 today and tell me the recipient should have received the original estimate.


## request.md

# Case 028: Amount received on an international payment

## Case details

- **Source role:** Perrin Wessel
- **Status:** Requires decision
- **Created:** 2026-11-18 09:00+00:00
- **Updated:** 2026-11-18 10:15+00:00
- **Operator:** Brackenfold Bank case desk

## Context

An authenticated sender asks about international payment INT-028 from SYN-ACCT-B028. The supplied recipient advice came through the customer.

## Initial request

Please compensate the EUR25 today and tell me the recipient should have received the original estimate.

## Decision point

No desk response to the final request is recorded. Using the complete history and supplied evidence, recommend the next action, recipient and communication, explaining uncertainty and confidence.

## History

[Read the complete event history](history.md)

## Attachments

- [execution-advice.pdf](attachments/execution-advice.pdf)
- [recipient-advice.pdf](attachments/recipient-advice.pdf)


## attachments/execution-advice.pdf

FICTIONAL FACSIMILE · SYNTHETIC EXERCISE
International payment execution advice
Issuer: Brackenfold Bank
Reference: INT-028
Sender: Perrin Wessel / SYN-ACCT-B028
Execution: 2026-11-18 09:08+00:00
Principal converted: GBP 1000.00
Executed rate: 1.1500 EUR per GBP
Gross transferred: EUR 1150.00
Separate sending-bank fee: GBP 5.00
Total account debit: GBP 1005.00
Charge option: SHA / Shared
Destination: SYN-ACCT-REC028
Synthetic exercise material | Page 1 of 1

## attachments/recipient-advice.pdf

FICTIONAL FACSIMILE · SYNTHETIC EXERCISE
Incoming payment advice
Issuer: Synthetic Overseas Recipient Bank
Recipient: Osa Melwick / SYN-ACCT-REC028
Reference: INT-028
Received: 2026-11-18 09:50+00:00
Gross amount: EUR 1150.00
Intermediary deduction reported: EUR 15.00
Net credited: EUR 1135.00
Advice issued: 2026-11-18 09:55+00:00
Synthetic exercise material | Page 1 of 1
