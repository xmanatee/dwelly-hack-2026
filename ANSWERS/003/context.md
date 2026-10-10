# Supplied case 003

## history.md

# Change of card-settlement account — history

Total events: 5

The opening internal note is the bank case view assembled during this contact; the CoP result was obtained after the customer supplied the new details. Earlier dates within the note refer to records, not to the creation time of the note. Events on the same day without individual timestamps follow the source conversation order.

<a id="event-001"></a>
## 2026-09-23 (individual event time not recorded) — event 001

- **Channel:** Internal account view
- **From:** Harrow & Vale Bank plc (case record)
- **To:** Servicing agent (Harrow & Vale Bank plc)

Customer: **Bramley Bakes Ltd** — business customer (two cafés). Accounts at H&V:
- **Trading account** SYN-SC-03-2 / SYN-ACCT-03-1, name "Bramley Bakes Limited" — card-acquirer settlements land here daily (H&V Merchant Services)
- **Savings account** SYN-SC-03-2 / SYN-ACCT-03-2

The company opened a new operating account at Revo Business in August. Card settlements are still landing in the H&V trading account: 16–22 Sep, £9,412.60 in total.

Mandate: changes to the merchant settlement account require instruction from an **authorised signatory** (S. Bramley, Director; R. Ahmed, Director). Chat user "claire.b" (office manager) holds *view + payments-create* only.

CoP check on the details supplied below: sort code SYN-SC-03-1 is a valid Revo Business sort code; account name check returns **"No match"** — the name held at that bank differs from the one given.

<a id="event-002"></a>
## 2026-09-23 (individual event time not recorded) — event 002

- **Channel:** Business banking chat
- **From:** Claire B. (office manager)
- **To:** Servicing agent (Harrow & Vale Bank plc)

Hi — we moved our day-to-day banking to Revo in August but the card machine money is still going into the old H&V account. Please update the settlement account to: SYN-ACCT-03-3, sort code SYN-SC-03-1, name **Bramley Bakers Limited**. And can you redirect last week's settlements (£9,412.60) to the new account — that's where we pay wages from on Friday.

<a id="event-003"></a>
## 2026-09-23 (individual event time not recorded) — event 003

- **Channel:** Business banking chat
- **From:** Servicing agent (Harrow & Vale Bank plc)
- **To:** Customer / caller

Thanks. Before anything changes on the settlement destination I need to go through a couple of things.

<a id="event-004"></a>
## 2026-09-23 (individual event time not recorded) — event 004

- **Channel:** Business banking chat
- **From:** Claire B.
- **To:** Servicing agent (Harrow & Vale Bank plc)

Sarah (director) confirmed this on the phone to me this morning, she's on a supplier visit all day. Can you do it now so tonight's settlement goes to the right place? She'll email you tomorrow.

<a id="event-005"></a>
## 2026-09-23 (individual event time not recorded) — event 005

- **Channel:** Business banking chat
- **From:** Claire B.
- **To:** Servicing agent (Harrow & Vale Bank plc)

Just so you have everything — the account you should be updating is SYN-SC-03-2 / SYN-ACCT-03-1, "Bramley Bakes Limited". That's the one, right?


## request.md

# Change of card-settlement account

## Case details

- **Source role:** Bank customer
- **Status:** Requires decision
- **Created:** 2026-09-23 (day precision)
- **Updated:** 2026-09-23 (day precision)
- **Bank:** Harrow & Vale Bank plc
- **Channel:** Business banking chat
- **Contact start:** 12:30 local UK time (individual message times not recorded)

## Initial request

Hi — we moved our day-to-day banking to Revo in August but the card machine money is still going into the old H&V account. Please update the settlement account to: SYN-ACCT-03-3, sort code SYN-SC-03-1, name **Bramley Bakers Limited**. And can you redirect last week's settlements (£9,412.60) to the new account — that's where we pay wages from on Friday.

## History

[Read the complete event history](history.md).

## Attachments

- [Confirmation of Payee result for the details supplied](attachments/cop_result.json)
- [users and permissions on the account mandate](attachments/mandate_extract.csv)
- [the customer's email request](attachments/request_from_claire.eml)
- [card-acquirer settlements 16–22 Sep and where they landed](attachments/settlement_history_16-22sep.csv)


## attachments/cop_result.json

{
  "request": {
    "sort_code": "SYN-SC-03-1",
    "account_number": "SYN-ACCT-03-3",
    "name_supplied": "Bramley Bakers Limited",
    "account_type": "business"
  },
  "response": {
    "matched": false,
    "reason_code": "ANNM",
    "reason": "Account name does not match",
    "name_at_bank": null,
    "bank": "Revo Business",
    "checked_at": "2026-09-23T11:31:09Z"
  }
}


## attachments/mandate_extract.csv

user_id,name,role_on_mandate,permissions,can_change_settlement_account
s.bramley,Sarah Bramley,Director (authorised signatory),view;payments_create;payments_approve;mandate_admin,yes (with second signatory)
r.ahmed,Rizwan Ahmed,Director (authorised signatory),view;payments_create;payments_approve;mandate_admin,yes (with second signatory)
claire.b,Claire Bennett,Office manager (user),view;payments_create,no


## attachments/request_from_claire.eml

From: Claire Bennett <claire@bramleybakes.example>
To: business.support@harrowvale.example
Subject: Update to card settlement account - urgent
Date: Wed, 23 Sep 2026 12:02:44 +0100
MIME-Version: 1.0
Content-Type: text/plain; charset=utf-8

Hi,

Please update the account our card takings settle into. We moved our day-to-day banking to Revo Business in August.

New details:
Account name: Bramley Bakers Limited
Sort code: SYN-SC-03-1
Account number: SYN-ACCT-03-3

Also please redirect last week's settlements (16-22 Sept, £9,412.60) to the new account - that is where wages go out from on Friday.

Sarah (director) has confirmed this with me by phone this morning, she is at a supplier all day.

Thanks,
Claire Bennett
Office Manager, Bramley Bakes Ltd


## attachments/settlement_history_16-22sep.csv

date,acquirer_batch,amount_gbp,credited_to
2026-09-16,HVMS-4471,1288.40,SYN-SC-03-2 / SYN-ACCT-03-1
2026-09-17,HVMS-4472,1402.15,SYN-SC-03-2 / SYN-ACCT-03-1
2026-09-18,HVMS-4473,1195.60,SYN-SC-03-2 / SYN-ACCT-03-1
2026-09-19,HVMS-4474,1731.05,SYN-SC-03-2 / SYN-ACCT-03-1
2026-09-20,HVMS-4475,1954.30,SYN-SC-03-2 / SYN-ACCT-03-1
2026-09-21,HVMS-4476,1041.10,SYN-SC-03-2 / SYN-ACCT-03-1
2026-09-22,HVMS-4477,800.00,SYN-SC-03-2 / SYN-ACCT-03-1
TOTAL,,9412.60,
