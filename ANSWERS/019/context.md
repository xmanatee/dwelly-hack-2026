# Supplied case 019

## history.md

# Duplicate payment to a cleaner — history

Total events: 4

The opening internal note is a snapshot available to the servicing agent at the time of contact; any earlier dates within it refer to records, not to the creation time of this note. Events on the same day without individual timestamps follow the source conversation order.

<a id="event-001"></a>
## 2026-09-23 (individual event time not recorded) — event 001

- **Channel:** Internal account view
- **From:** Harrow & Vale Bank plc (case record)
- **To:** Servicing agent (Harrow & Vale Bank plc)

Customer: **Linda Ferris** — personal current account (landlord; her property at 53 Winchester Road is managed by Oakfield PM).
| Date | Event |
|---|---|
| 12 Aug | Debit −£651.00, Faster Payment to CO-CLEAN SERVICES LTD, ref "INV 4471 53 WINCHESTER", new payee (CoP match at the time) |

Customer states the managing agency also paid Co-Clean's invoice 4471 from her rental funds on 15 Aug, so the contractor was paid twice. She spoke to Co-Clean on 17 Sep; they agreed to refund £651 "on the next payment run".

<a id="event-002"></a>
## 2026-09-23 (individual event time not recorded) — event 002

- **Channel:** In-app chat (personal banking)
- **From:** Customer
- **To:** Servicing agent (Harrow & Vale Bank plc)

I paid an end-of-tenancy cleaner £651 on 12 August and it turns out my letting agent paid the same invoice from my rent. Co-Clean have agreed to refund one of them but it's been a week. Can you recall the payment from your side so I get it back faster?

<a id="event-003"></a>
## 2026-09-23 (individual event time not recorded) — event 003

- **Channel:** In-app chat (personal banking)
- **From:** Servicing agent (Harrow & Vale Bank plc)
- **To:** Customer / caller

Let me look at the payment and explain what a recall would and wouldn't do here.

<a id="event-004"></a>
## 2026-09-23 (individual event time not recorded) — event 004

- **Channel:** In-app chat (personal banking)
- **From:** Customer
- **To:** Servicing agent (Harrow & Vale Bank plc)

It was a duplicate payment, isn't that exactly what recalls are for?


## request.md

# Duplicate payment to a cleaner

## Case details

- **Source role:** Bank customer
- **Status:** Requires decision
- **Created:** 2026-09-23 (day precision)
- **Updated:** 2026-09-23 (day precision)
- **Bank:** Harrow & Vale Bank plc
- **Channel:** In-app chat (personal banking)

## Initial request

I paid an end-of-tenancy cleaner £651 on 12 August and it turns out my letting agent paid the same invoice from my rent. Co-Clean have agreed to refund one of them but it's been a week. Can you recall the payment from your side so I get it back faster?

## History

[Read the complete event history](history.md).

## Attachments

- [extract from the agency's landlord statement (supplied by customer)](attachments/agency_statement_extract.txt)
- [contractor's email agreeing the refund (forwarded by customer)](attachments/coclean_refund_agreement.eml)
- [bank payment confirmation for the 12 Aug payment (PDF)](attachments/payment_confirmation_2026-08-12.pdf)


## attachments/agency_statement_extract.txt

[Extract from Oakfield PM landlord statement, 53 Winchester Road, August 2026 - supplied by customer]
15/08/2026  Contractor payment - Co-Clean Services Ltd - inv 4471 end of tenancy clean   -£651.00


## attachments/coclean_refund_agreement.eml

From: Co-Clean Services <accounts@co-clean.example>
To: linda.ferris@example.net
Subject: RE: Invoice 4471 paid twice
Date: Thu, 17 Sep 2026 14:05:31 +0100
MIME-Version: 1.0
Content-Type: text/plain; charset=utf-8

Hi Linda,

You're right, we received £651 from you on 12 August and another £651 from Oakfield PM on 15 August against invoice 4471. Apologies for not spotting it. We'll refund £651 to you on our next payment run.

Regards,
Dean
Co-Clean Services Ltd


## attachments/payment_confirmation_2026-08-12.pdf

Harrow & Vale Bank plc
harrowvale.example
Mrs Linda Ferris 12 August 2026
Faster Payment HV26081210144802
Payment confirmation
This confirms that the following payment was sent from your account and received by the beneficiary bank.
Field Value
Date / time 12 Aug 2026 10:14
Amount £651.00
Payee CO-CLEAN SERVICES LTD
Sort code / account
Reference INV 4471 53 WINCHESTER
Status Completed
This document is a confirmation of payment and not a receipt from the beneficiary.
Customer Services, Example PO Box, Leeds ZZ1 1ZZ
Account SYN-ACCT-19-1
SYNTHETIC ROUTING WITHHELD
