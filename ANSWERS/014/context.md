# Supplied case 014

## history.md

# Two card payments to an agency — history

Total events: 4

The opening internal note is a snapshot available to the servicing agent at the time of contact; any earlier dates within it refer to records, not to the creation time of this note. Events on the same day without individual timestamps follow the source conversation order.

<a id="event-001"></a>
## 2026-09-16 (individual event time not recorded) — event 001

- **Channel:** Internal account view
- **From:** Harrow & Vale Bank plc (case record)
- **To:** Servicing agent (Harrow & Vale Bank plc)

Customer: **Tomás Ribeiro** — personal current account, debit card.
| Date | Merchant | Amount |
|---|---|---|
| 11 Sep 18:02 | PAYGATE*NORTHGATE LET | −£634.00 |
| 11 Sep 18:04 | PAYGATE*NORTHGATE LET | −£634.00 |

Customer states he clicked the agency's payment link twice after a "page not responding" message. He has an email from the agency dated 14 Sep: "We can see the duplicate holding deposit and will refund £634 within 5–10 working days."

<a id="event-002"></a>
## 2026-09-16 (individual event time not recorded) — event 002

- **Channel:** In-app chat (personal banking)
- **From:** Customer
- **To:** Servicing agent (Harrow & Vale Bank plc)

I paid a holding deposit for a flat and it went through twice — £634 each. The agency said they'd refund it in 5–10 working days but that was two days ago and I need the money for the actual deposit. Can you just do a chargeback on the second one now? I've read that I'm entitled to it.

<a id="event-003"></a>
## 2026-09-16 (individual event time not recorded) — event 003

- **Channel:** In-app chat (personal banking)
- **From:** Servicing agent (Harrow & Vale Bank plc)
- **To:** Customer / caller

I can see both payments. Let me explain how a chargeback would work here and whether it's the fastest route.

<a id="event-004"></a>
## 2026-09-16 (individual event time not recorded) — event 004

- **Channel:** In-app chat (personal banking)
- **From:** Customer
- **To:** Servicing agent (Harrow & Vale Bank plc)

I don't want to wait 10 days for an agency to get round to it.


## request.md

# Two card payments to an agency

## Case details

- **Source role:** Bank customer
- **Status:** Requires decision
- **Created:** 2026-09-16 (day precision)
- **Updated:** 2026-09-16 (day precision)
- **Bank:** Harrow & Vale Bank plc
- **Channel:** In-app chat (personal banking)

## Initial request

I paid a holding deposit for a flat and it went through twice — £634 each. The agency said they'd refund it in 5–10 working days but that was two days ago and I need the money for the actual deposit. Can you just do a chargeback on the second one now? I've read that I'm entitled to it.

## History

[Read the complete event history](history.md).

## Attachments

- [agency email promising the refund (forwarded by customer)](attachments/agency_refund_email.eml)
- [the two card transactions](attachments/card_transactions.csv)


## attachments/agency_refund_email.eml

From: Northgate Lettings <accounts@northgate-lettings.example>
To: tomas.ribeiro@example.net
Subject: RE: Holding deposit paid twice - 9 Lime Grove
Date: Mon, 14 Sep 2026 15:22:10 +0100
MIME-Version: 1.0
Content-Type: text/plain; charset=utf-8

Hi Tomás,

Apologies - we can see the duplicate holding deposit of £634.00 taken on 11 September. Our payments team will refund one payment to the card it was paid from within 5-10 working days. You will see it as a refund from PAYGATE on your statement.

Kind regards,
Nicole
Northgate Lettings


## attachments/card_transactions.csv

date_time,merchant,mcc,amount,status,auth_code
2026-09-11 18:02:37,PAYGATE*NORTHGATE LET,6513 Real estate agents,-634.00,settled 2026-09-13,A71C02
2026-09-11 18:04:12,PAYGATE*NORTHGATE LET,6513 Real estate agents,-634.00,settled 2026-09-13,A71C09
