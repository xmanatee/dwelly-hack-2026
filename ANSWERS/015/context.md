# Supplied case 015

## history.md

# Unexpected first rent collection — history

Total events: 4

The opening internal note is a snapshot available to the servicing agent at the time of contact; any earlier dates within it refer to records, not to the creation time of this note. Events on the same day without individual timestamps follow the source conversation order.

<a id="event-001"></a>
## 2026-09-14 (individual event time not recorded) — event 001

- **Channel:** Internal account view
- **From:** Harrow & Vale Bank plc (case record)
- **To:** Servicing agent (Harrow & Vale Bank plc)

Customer: **Tunde Okoye** — personal current account.
| Date | Event |
|---|---|
| 28 Aug | Faster Payment −£4,980.00 to HARROW & VALE RE LIME PROPERTY CA, ref "MOVE IN 14 GROVE" (advance tenancy payment; bank record does not show how the agency allocated it) |
| 2 Sep | DD mandate H&V COLLECT / LIME PROPERTY created via originator invite |
| 9 Sep | Advance notice (originator copy): "£4,980.00 will be collected on 14 September, then £795.00 monthly" |
| 14 Sep | DD collection −£4,980.00 — paid; account now £3,100 overdrawn (arranged limit £1,000; unarranged portion incurs daily fee) |

Monthly rent per the customer: £795. The customer says he did not read the advance notice email.

<a id="event-002"></a>
## 2026-09-14 (individual event time not recorded) — event 002

- **Channel:** Phone (personal banking)
- **From:** Customer
- **To:** Servicing agent (Harrow & Vale Bank plc)

[ID&V passed] The letting agency has just taken nearly five grand out of my account by direct debit! I paid all the move-in money by bank transfer two weeks ago. My rent is £795. I'm massively overdrawn now. I want it all back today under the guarantee and I want that direct debit cancelled so they can never do this again.

<a id="event-003"></a>
## 2026-09-14 (individual event time not recorded) — event 003

- **Channel:** Phone (personal banking)
- **From:** Servicing agent (Harrow & Vale Bank plc)
- **To:** Customer / caller

I'm sorry — that's a large amount to have taken unexpectedly. Let me look at the mandate and the notice.

<a id="event-004"></a>
## 2026-09-14 (individual event time not recorded) — event 004

- **Channel:** Phone (personal banking)
- **From:** Customer
- **To:** Servicing agent (Harrow & Vale Bank plc)

I don't care what the notice said, I never agreed to £4,980 by direct debit.


## request.md

# Unexpected first rent collection

## Case details

- **Source role:** Bank customer
- **Status:** Requires decision
- **Created:** 2026-09-14 (day precision)
- **Updated:** 2026-09-14 (day precision)
- **Bank:** Harrow & Vale Bank plc
- **Channel:** Phone (personal banking)

## Initial request

The letting agency has just taken nearly five grand out of my account by direct debit! I paid all the move-in money by bank transfer two weeks ago. My rent is £795. I'm massively overdrawn now. I want it all back today under the guarantee and I want that direct debit cancelled so they can never do this again.

## History

[Read the complete event history](history.md).

## Attachments

- [Direct Debit advance notice (originator copy)](attachments/dd_advance_notice_2026-09-09.eml)
- [bank payment confirmation for the move-in transfer (PDF)](attachments/payment_confirmation_2026-08-28.pdf)
- [statement extract](attachments/statement_extract.csv)


## attachments/dd_advance_notice_2026-09-09.eml

From: Lime Property via H&V Collect <notices@hvcollect.example>
To: t.okoye@example.net
Subject: Advance notice of your Direct Debit - Lime Property
Date: Wed, 09 Sep 2026 07:30:00 +0100
MIME-Version: 1.0
Content-Type: text/plain; charset=utf-8

Dear Tunde Okoye,

Your Direct Debit to Lime Property (Hull) Ltd, reference LP-14GROVE-0208, has been set up.

First collection: £4,980.00 on 14 September 2026 (balance of your account as at 8 September)
Then: £795.00 monthly on the 14th

If you believe any amount is incorrect, please contact Lime Property before the collection date.


## attachments/payment_confirmation_2026-08-28.pdf

Harrow & Vale Bank plc
harrowvale.example
Mr Tunde Okoye 28 August 2026
Faster Payment HV26082811320471
Payment confirmation
This confirms that the following payment was sent from your account and received by the beneficiary bank.
Field Value
Date / time 28 Aug 2026 11:32
Amount £4,980.00
Payee HARROW & VALE RE LIME PROPERTY CA
Sort code / account
Reference MOVE IN 14 GROVE
Status Completed
This document is a confirmation of payment and not a receipt from the beneficiary.
Customer Services, Example PO Box, Leeds ZZ1 1ZZ
Account SYN-ACCT-15-1
SYNTHETIC ROUTING WITHHELD

## attachments/statement_extract.csv

date,type,description,amount,balance
2026-08-28,FP,HARROW & VALE RE LIME PROPERTY CA  MOVE IN 14 GROVE,-4980.00,1902.30
2026-09-02,INFO,DIRECT DEBIT INSTRUCTION SET UP: LIME PROPERTY (LP-14GROVE-0208),0.00,1902.30
2026-09-14,DD,H&V COLLECT / LIME PROPERTY  LP-14GROVE-0208,-4980.00,-3077.70
2026-09-14,FEE,UNARRANGED OVERDRAFT DAILY FEE,-6.50,-3084.20
