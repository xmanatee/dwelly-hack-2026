# Supplied case 017

## history.md

# Statement balance query — history

Total events: 4

The opening internal note is a snapshot available to the servicing agent at the time of contact; any earlier dates within it refer to records, not to the creation time of this note. Events on the same day without individual timestamps follow the source conversation order.

<a id="event-001"></a>
## 2026-09-30 (individual event time not recorded) — event 001

- **Channel:** Internal account view
- **From:** Harrow & Vale Bank plc (case record)
- **To:** Servicing agent (Harrow & Vale Bank plc)

Customer: **Bright Sparks Electrical Ltd** — business current account SYN-SC-17-1 / SYN-ACCT-17-1. The bookkeeper reconciles daily from a CSV export downloaded from Business Online.

Their figures for 29 Sep: opening £32,113.84 (their 28 Sep close), supplier payments £8,415.30, credits per their CSV £30,078.94, closing £55,527.48 (the balance on screen when they looked).

Bank's view of 29 Sep:
- CSV export requested by user violetta.k at **13:15:02**.
- Credits **after 13:15** on 29 Sep: +£1,750.00 at 14:02 (K WHITTLE, ref "INV 4471"), +£120.00 at 16:41 (A ROSS, ref "INV 4480 PART").
- The closing balance they quote matches the running balance **between 14:02 and 16:41** (read from the screen mid-afternoon), not at 13:15.
- Same pattern the day before: +£1,900.00 landed at 18:10 on 28 Sep, after their 13:20 export.

<a id="event-002"></a>
## 2026-09-30 (individual event time not recorded) — event 002

- **Channel:** Business banking chat
- **From:** Violetta (bookkeeper)
- **To:** Servicing agent (Harrow & Vale Bank plc)

Hi, we're £1,750 out on yesterday's balancing and we think a credit is missing from your statement. Our download shows £30,078.94 of credits but the closing balance only works if credits were £31,828.94. Can you investigate a missing payment? Round number — we think something's been lost.

<a id="event-003"></a>
## 2026-09-30 (individual event time not recorded) — event 003

- **Channel:** Business banking chat
- **From:** Servicing agent (Harrow & Vale Bank plc)
- **To:** Customer / caller

I'll compare your export with the account's full-day activity.

<a id="event-004"></a>
## 2026-09-30 (individual event time not recorded) — event 004

- **Channel:** Business banking chat
- **From:** Violetta
- **To:** Servicing agent (Harrow & Vale Bank plc)

Our director wants this logged as a formal missing-funds complaint if it isn't found today.


## request.md

# Statement balance query

## Case details

- **Source role:** Bank customer
- **Status:** Requires decision
- **Created:** 2026-09-30 (day precision)
- **Updated:** 2026-09-30 (day precision)
- **Bank:** Harrow & Vale Bank plc
- **Channel:** Business banking chat
- **Contact start:** 09:40 local UK time (individual message times not recorded)

## Initial request

Hi, we're £1,750 out on yesterday's balancing and we think a credit is missing from your statement. Our download shows £30,078.94 of credits but the closing balance only works if credits were £31,828.94. Can you investigate a missing payment? Round number — we think something's been lost.

## History

[Read the complete event history](history.md).

## Attachments

- [the customer's reconciliation working](attachments/bookkeeper_reconciliation_2026-09-29.csv)
- [the customer's download](attachments/export_2026-09-29_1315.csv)
- [bank's end-of-day view](attachments/full_day_2026-09-29.csv)


## attachments/bookkeeper_reconciliation_2026-09-29.csv

line,description,amount
1,Opening balance (our 28 Sep close),32113.84
2,Credits per CSV export (4 items),30078.94
3,Supplier batch 2909,-8415.30
4,Expected closing (1+2+3),53777.48
5,Closing balance shown on screen,55527.48
6,Difference (5-4),1750.00
note,"Export taken 13:15; balance noted from Business Online dashboard later that afternoon",


## attachments/export_2026-09-29_1315.csv

exported_at,2026-09-29T13:15:02
timestamp,type,amount,counterparty,reference,running_balance
2026-09-29T00:04:11,credit,875.00,J MORGAN,INV 4462,32988.84
2026-09-29T06:12:40,credit,1200.00,CARDNET SETTLEMENT,2809,34188.84
2026-09-29T09:31:05,credit,27343.94,HALDANE HOMES LTD,INV 4455 STAGE 2,61532.78
2026-09-29T10:20:30,credit,660.00,S AHMED,INV 4470,62192.78
2026-09-29T11:05:12,debit,-8415.30,SUPPLIER BATCH 2909,,53777.48


## attachments/full_day_2026-09-29.csv

timestamp,type,amount,counterparty,reference,running_balance
2026-09-28T18:10:22,credit,1900.00,P LEWIS,INV 4461,32113.84
2026-09-29T00:04:11,credit,875.00,J MORGAN,INV 4462,32988.84
2026-09-29T06:12:40,credit,1200.00,CARDNET SETTLEMENT,2809,34188.84
2026-09-29T09:31:05,credit,27343.94,HALDANE HOMES LTD,INV 4455 STAGE 2,61532.78
2026-09-29T10:20:30,credit,660.00,S AHMED,INV 4470,62192.78
2026-09-29T11:05:12,debit,-8415.30,SUPPLIER BATCH 2909,,53777.48
2026-09-29T14:02:47,credit,1750.00,K WHITTLE,INV 4471,55527.48
2026-09-29T16:41:09,credit,120.00,A ROSS,INV 4480 PART,55647.48
