# Supplied case 004

## history.md

# Two rent payments in one month — history

Total events: 4

The opening internal note is a snapshot available to the servicing agent at the time of contact; any earlier dates within it refer to records, not to the creation time of this note. Events on the same day without individual timestamps follow the source conversation order.

<a id="event-001"></a>
## 2026-09-04 (individual event time not recorded) — event 001

- **Channel:** Internal account view
- **From:** Harrow & Vale Bank plc (case record)
- **To:** Servicing agent (Harrow & Vale Bank plc)

Customer: **Priya Desai** — personal current account.
| Date | Type | Amount | Detail |
|---|---|---|---|
| 1 Sep | Standing order | −£1,000.00 | to HARROW & VALE RE HARBOUR LETS LTD CA, ref "RENT 27 ELM RD" (SO set up Feb 2025, 1st of month) |
| 3 Sep | Direct Debit | −£900.00 | H&V COLLECT / HARBOUR LETS — mandate created 20 Aug 2026 via originator invite |

Direct Debit advance notice (originator copy visible to bank): sent 24 Aug — "£900.00 will be collected on or around 3 September, then monthly". Collection amount matches the notice. The standing order is still active for 1 Oct.

<a id="event-002"></a>
## 2026-09-04 (individual event time not recorded) — event 002

- **Channel:** In-app chat (personal banking)
- **From:** Customer
- **To:** Servicing agent (Harrow & Vale Bank plc)

My rent's been taken twice — £1,000 on the 1st and £900 on the 3rd. I want the £900 refunded under the Direct Debit Guarantee today and the direct debit cancelled. I never agreed to £900, my rent is £1,000 — they've got the amount wrong.

<a id="event-003"></a>
## 2026-09-04 (individual event time not recorded) — event 003

- **Channel:** In-app chat (personal banking)
- **From:** Servicing agent (Harrow & Vale Bank plc)
- **To:** Customer / caller

I can see both payments. Let me explain what each one is and what the options are.

<a id="event-004"></a>
## 2026-09-04 (individual event time not recorded) — event 004

- **Channel:** In-app chat (personal banking)
- **From:** Customer
- **To:** Servicing agent (Harrow & Vale Bank plc)

I don't want options, the guarantee says you refund immediately if there's an error. This is an error.


## request.md

# Two rent payments in one month

## Case details

- **Source role:** Bank customer
- **Status:** Requires decision
- **Created:** 2026-09-04 (day precision)
- **Updated:** 2026-09-04 (day precision)
- **Bank:** Harrow & Vale Bank plc
- **Channel:** In-app chat (personal banking)

## Initial request

My rent's been taken twice — £1,000 on the 1st and £900 on the 3rd. I want the £900 refunded under the Direct Debit Guarantee today and the direct debit cancelled. I never agreed to £900, my rent is £1,000 — they've got the amount wrong.

## History

[Read the complete event history](history.md).

## Attachments

- [Direct Debit advance notice (originator copy)](attachments/dd_advance_notice_2026-08-24.eml)
- [standing order record on file](attachments/standing_order_on_file.json)
- [statement extract, September](attachments/statement_extract_sep.csv)


## attachments/dd_advance_notice_2026-08-24.eml

From: Harbour Lets via H&V Collect <notices@hvcollect.example>
To: priya.desai@example.net
Subject: Advance notice: your first Direct Debit to Harbour Lets Ltd
Date: Mon, 24 Aug 2026 09:12:00 +0100
MIME-Version: 1.0
Content-Type: text/plain; charset=utf-8

Dear Priya Desai,

You have set up a Direct Debit to Harbour Lets Ltd (reference HL-27ELM-0091).

First collection: £900.00 on or around 3 September 2026
Then: £900.00 monthly on or around the 3rd

If you currently pay this rent by standing order, please cancel the standing order with your bank before the first collection to avoid paying twice.

The Direct Debit Guarantee applies to this Direct Debit.


## attachments/standing_order_on_file.json

{
  "payee": "HARROW & VALE RE HARBOUR LETS LTD CA",
  "sort_code": "SYN-SC-04-1",
  "account_number": "SYN-ACCT-04-1",
  "reference": "RENT 27 ELM RD",
  "amount": 1000.0,
  "frequency": "monthly",
  "next_payment": "2026-10-01",
  "created": "2025-02-01",
  "status": "active"
}


## attachments/statement_extract_sep.csv

date,type,description,amount,balance
2026-09-01,SO,HARROW & VALE RE HARBOUR LETS LTD CA  RENT 27 ELM RD,-1000.00,1642.18
2026-09-03,DD,H&V COLLECT / HARBOUR LETS  HL-27ELM-0091,-900.00,742.18
