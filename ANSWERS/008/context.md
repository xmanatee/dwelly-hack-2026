# Supplied case 008

## history.md

# New rent payment details — history

Total events: 4

The opening internal note is the bank case view assembled during this contact; the CoP result was obtained after the customer supplied the new details. Earlier dates within the note refer to records, not to the creation time of the note. Events on the same day without individual timestamps follow the source conversation order.

<a id="event-001"></a>
## 2026-09-23 (individual event time not recorded) — event 001

- **Channel:** Internal account view
- **From:** Harrow & Vale Bank plc (case record)
- **To:** Servicing agent (Harrow & Vale Bank plc)

Customer: **Nicole Hart** — personal current account. Standing order £1,150 on the 25th to "Miss D L Hanlon", Meridian Bank SYN-SC-08-1 / SYN-ACCT-08-2, ref "RENT 26 BROAD LANE", active since March 2025, never failed.

The customer has pasted an email she received this morning from `dl.hanlon.property@sender.example`. Her landlord's previous emails (per the customer) came from a different address. CoP on the new details in the email: **No match — account name held is "DLH PROPERTY SERVICES LTD"**.

<a id="event-002"></a>
## 2026-09-23 (individual event time not recorded) — event 002

- **Channel:** In-app chat (personal banking)
- **From:** Customer
- **To:** Servicing agent (Harrow & Vale Bank plc)

Hi, my landlord's emailed to say she's changed banks. Please can you update my rent standing order to: sort code SYN-SC-08-2, account SYN-ACCT-08-1, Miss D L Hanlon. It goes on the 25th so needs doing today. Email below.

> *"Hi Nicole, quick one — I've switched banks and closed my old account, so please send this month's rent to my new account: SYN-SC-08-2 / SYN-ACCT-08-1. Sorry for the short notice, the old one closes today so anything sent there will bounce. Thanks, Debbie"*

<a id="event-003"></a>
## 2026-09-23 (individual event time not recorded) — event 003

- **Channel:** In-app chat (personal banking)
- **From:** Servicing agent (Harrow & Vale Bank plc)
- **To:** Customer / caller

Thanks for sending the email. Before I change the payee I need to tell you what Confirmation of Payee came back with.

<a id="event-004"></a>
## 2026-09-23 (individual event time not recorded) — event 004

- **Channel:** In-app chat (personal banking)
- **From:** Customer
- **To:** Servicing agent (Harrow & Vale Bank plc)

Oh — she did mention going limited at some point. It'll be her. Can you just override it? She's been my landlord for years.


## request.md

# New rent payment details

## Case details

- **Source role:** Bank customer
- **Status:** Requires decision
- **Created:** 2026-09-23 (day precision)
- **Updated:** 2026-09-23 (day precision)
- **Bank:** Harrow & Vale Bank plc
- **Channel:** In-app chat (personal banking)
- **Contact start:** 11:10 local UK time (individual message times not recorded)

## Initial request

Hi, my landlord's emailed to say she's changed banks. Please can you update my rent standing order to: sort code SYN-SC-08-2, account SYN-ACCT-08-1, Miss D L Hanlon. It goes on the 25th so needs doing today. Email below.

## History

[Read the complete event history](history.md).

## Attachments

- [Confirmation of Payee result for the new details](attachments/cop_result_new_details.json)
- [customer's note of previous emails from the landlord](attachments/customer_previous_landlord_emails.txt)
- [the landlord email, with headers, as forwarded by the customer](attachments/landlord_email_as_forwarded.eml)
- [standing order record on file](attachments/standing_order_on_file.json)


## attachments/cop_result_new_details.json

{
  "request": {
    "sort_code": "SYN-SC-08-2",
    "account_number": "SYN-ACCT-08-1",
    "name_supplied": "Miss D L Hanlon",
    "account_type": "personal"
  },
  "response": {
    "matched": false,
    "reason_code": "ANNM",
    "reason": "Account name does not match",
    "name_at_bank": "DLH PROPERTY SERVICES LTD",
    "account_type_at_bank": "business",
    "checked_at": "2026-09-23T10:12:02Z"
  }
}


## attachments/customer_previous_landlord_emails.txt

[Customer's note: previous emails from Debbie, for comparison]
2025-03-04  From: debbie.hanlon@btinternet.example  Subject: Welcome to 26 Broad Lane - rent details
2025-12-18  From: debbie.hanlon@btinternet.example  Subject: Boiler service Jan
2026-06-02  From: debbie.hanlon@btinternet.example  Subject: Rent review - no change this year


## attachments/landlord_email_as_forwarded.eml

From: Debbie Hanlon <dl.hanlon.property@sender.example>
To: nicole.hart@example.net
Subject: New bank details for rent
Date: Wed, 23 Sep 2026 07:48:19 +0100
Reply-To: dlh.accounts.desk@reply.example
X-Mailer: Webmail
Received: from mail.sender.example by mx.example.net; Wed, 23 Sep 2026 07:48:21 +0100
MIME-Version: 1.0
Content-Type: text/plain; charset=utf-8

Hi Nicole, quick one - I've switched banks and closed my old account, so please send this month's rent to my new account: SYN-SC-08-2 / SYN-ACCT-08-1. Sorry for the short notice, the old one closes today so anything sent there will bounce.

Thanks,
Debbie


## attachments/standing_order_on_file.json

{
  "payee": "Miss D L Hanlon",
  "bank": "Meridian Bank",
  "sort_code": "SYN-SC-08-1",
  "account_number": "SYN-ACCT-08-2",
  "reference": "RENT 26 BROAD LANE",
  "amount": 1150.0,
  "day_of_month": 25,
  "created": "2025-03-10",
  "cop_at_creation": "matched",
  "last_payment": "2026-08-25",
  "failures": 0
}
