# Supplied case 009

## history.md

# Request to close a current account — history

Total events: 4

The opening internal note is a snapshot available to the servicing agent at the time of contact; any earlier dates within it refer to records, not to the creation time of this note. Events on the same day without individual timestamps follow the source conversation order.

<a id="event-001"></a>
## 2026-09-21 (individual event time not recorded) — event 001

- **Channel:** Internal account view
- **From:** Harrow & Vale Bank plc (case record)
- **To:** Servicing agent (Harrow & Vale Bank plc)

Customer: **Owen Price** — personal current account at H&V, balance £12.40. Customer opened an account at another bank in August and moved his salary there **manually** (no Current Account Switch Service request on file).

Still attached to the H&V account:
| Item | Detail |
|---|---|
| Direct Debit | Meridian Motor Insurance, £68.20, next collection **1 Oct** |
| Direct Debit | FitLife Gyms, £45.00, next collection 1 Oct |
| Standing order | £200 to "S PRICE", 28th monthly (customer says: money to his mum) |
| Inbound | Employer expense reimbursements still arrive here (last one 14 Sep, £83.10) |

Closure policy: an account with active DDs/SOs can be closed on instruction, but the bank must warn that they will fail; CASS full switch (redirects payments in and out for 3 years) is available at the new bank's request within 7 working days.

<a id="event-002"></a>
## 2026-09-21 (individual event time not recorded) — event 002

- **Channel:** Phone (personal banking)
- **From:** Customer
- **To:** Servicing agent (Harrow & Vale Bank plc)

[ID&V passed] I want to close my account with you today. I've moved everything to my new bank in August, salary's going there now. Just close it and send me whatever's left.

<a id="event-003"></a>
## 2026-09-21 (individual event time not recorded) — event 003

- **Channel:** Phone (personal banking)
- **From:** Servicing agent (Harrow & Vale Bank plc)
- **To:** Customer / caller

I can arrange that. Can I check a few things that are still attached to the account first?

<a id="event-004"></a>
## 2026-09-21 (individual event time not recorded) — event 004

- **Channel:** Phone (personal banking)
- **From:** Customer
- **To:** Servicing agent (Harrow & Vale Bank plc)

There's nothing on it, I moved it all. Close it. And if anything does come in, just forward it to my new account — here are the details.


## request.md

# Request to close a current account

## Case details

- **Source role:** Bank customer
- **Status:** Requires decision
- **Created:** 2026-09-21 (day precision)
- **Updated:** 2026-09-21 (day precision)
- **Bank:** Harrow & Vale Bank plc
- **Channel:** Phone (personal banking)

## Initial request

I want to close my account with you today. I've moved everything to my new bank in August, salary's going there now. Just close it and send me whatever's left.

## History

[Read the complete event history](history.md).

## Attachments

- [mandates and recurring items on the account](attachments/account_summary.csv)
- [text of the insurer's letter (forwarded by customer)](attachments/insurer_reminder_letter.txt)


## attachments/account_summary.csv

item,type,counterparty,amount,next_date,status
Direct Debit,DD,MERIDIAN MOTOR INSURANCE (policy MMI-44-88120),68.20,2026-10-01,active
Direct Debit,DD,FITLIFE GYMS LTD,45.00,2026-10-01,active
Standing order,SO,S PRICE (ref MUM),200.00,2026-09-28,active
Inbound credit,CR,ELMSTEAD LOGISTICS LTD - EXPENSES,83.10,last 2026-09-14,recurring (irregular)
Balance,,,12.40,,
CASS switch request,,,,none on file,


## attachments/insurer_reminder_letter.txt

[Customer forwarded - text of letter from Meridian Motor Insurance dated 15 Sep 2026]
Policy MMI-44-88120 - Ford Fiesta - annual premium paid monthly by Direct Debit, £68.20 on the 1st.
Important: if a monthly payment is not received we will write to you and, if it remains unpaid after 14 days, your policy will be cancelled. Driving without insurance is a criminal offence.
