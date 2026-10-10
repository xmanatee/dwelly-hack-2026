# Supplied case 011

## history.md

# Refund after a duplicate payment — history

Total events: 4

The opening internal note is a snapshot available to the servicing agent at the time of contact; any earlier dates within it refer to records, not to the creation time of this note. Events on the same day without individual timestamps follow the source conversation order.

<a id="event-001"></a>
## 2026-09-23 (individual event time not recorded) — event 001

- **Channel:** Internal account view
- **From:** Harrow & Vale Bank plc (case record)
- **To:** Servicing agent (Harrow & Vale Bank plc)

Customer: **Paul Devlin t/a Devlin Plumbing** — sole-trader business account SYN-SC-11-1 / SYN-ACCT-11-1.
| Date | Event |
|---|---|
| 21 Sep 09:40 | Credit +£1,096.00, Faster Payment, payer name "A KOWALCZYK" (Meridian SYN-SC-11-2 / SYN-ACCT-11-2), ref "INV 2211 BOILER" |
| 22 Sep 14:20 | Credit +£1,096.00, Faster Payment, payer name "A KOWALCZYK" (Meridian SYN-SC-11-2 / SYN-ACCT-11-2), ref "INV 2211 BOILER" |

Customer's request (below) gives refund details: SYN-SC-11-2 / SYN-ACCT-11-2, name **M. Kowalczyk**. CoP on those details: **Match — "M KOWALCZYK"**.

<a id="event-002"></a>
## 2026-09-23 (individual event time not recorded) — event 002

- **Channel:** Business banking chat
- **From:** Paul D.
- **To:** Servicing agent (Harrow & Vale Bank plc)

Hi, a customer paid my invoice twice by mistake — £1,096 on Monday and again yesterday. She's texted me: "please send it back to my husband's account, SYN-ACCT-11-2, SYN-SC-11-2, M Kowalczyk, that's what I paid from". Can you refund one of them to that?

<a id="event-003"></a>
## 2026-09-23 (individual event time not recorded) — event 003

- **Channel:** Business banking chat
- **From:** Servicing agent (Harrow & Vale Bank plc)
- **To:** Customer / caller

I can see both payments. One thing before I send anything — the payer on the credits shows as "A Kowalczyk" and the refund name you've given is "M Kowalczyk".

<a id="event-004"></a>
## 2026-09-23 (individual event time not recorded) — event 004

- **Channel:** Business banking chat
- **From:** Paul D.
- **To:** Servicing agent (Harrow & Vale Bank plc)

Yeah, Anna's the customer, Marek's her husband, it's their joint money. She says the account's his but she uses it. I don't want to send it to the wrong place, but I also don't want to sit on their money.


## request.md

# Refund after a duplicate payment

## Case details

- **Source role:** Bank customer
- **Status:** Requires decision
- **Created:** 2026-09-23 (day precision)
- **Updated:** 2026-09-23 (day precision)
- **Bank:** Harrow & Vale Bank plc
- **Channel:** Business banking chat

## Initial request

Hi, a customer paid my invoice twice by mistake — £1,096 on Monday and again yesterday. She's texted me: "please send it back to my husband's account, SYN-ACCT-11-2, SYN-SC-11-2, M Kowalczyk, that's what I paid from". Can you refund one of them to that?

## History

[Read the complete event history](history.md).

## Attachments

- [the client's text, forwarded by the customer](attachments/client_text_message.txt)
- [Confirmation of Payee result for the refund details](attachments/cop_result_refund_details.json)
- [the two inbound payment messages](attachments/inbound_payments.json)


## attachments/client_text_message.txt

[Text from client, forwarded by Paul Devlin]
Tue 22 Sep 19:02, from +44 7700 900 415 (saved as "Anna K - boiler job")
"Hi Paul, so sorry - I paid your invoice twice, the app glitched. Please can you send one back to my husband's account, that's what I paid from: SYN-ACCT-11-2, SYN-SC-11-2, M Kowalczyk. Thank you!"


## attachments/cop_result_refund_details.json

{
  "request": {
    "sort_code": "SYN-SC-11-2",
    "account_number": "SYN-ACCT-11-2",
    "name_supplied": "M Kowalczyk",
    "account_type": "personal"
  },
  "response": {
    "matched": true,
    "name_at_bank": "M KOWALCZYK",
    "checked_at": "2026-09-23T10:05:33Z"
  }
}


## attachments/inbound_payments.json

[
  {
    "received": "2026-09-21T09:40:12+01:00",
    "amount": 1096.0,
    "payer_name_text": "A KOWALCZYK",
    "payer_sort_code": "SYN-SC-11-2",
    "payer_account": "SYN-ACCT-11-2",
    "payer_bank": "Meridian Bank",
    "reference": "INV 2211 BOILER",
    "end_to_end_id": "MER26092109401201"
  },
  {
    "received": "2026-09-22T14:20:48+01:00",
    "amount": 1096.0,
    "payer_name_text": "A KOWALCZYK",
    "payer_sort_code": "SYN-SC-11-2",
    "payer_account": "SYN-ACCT-11-2",
    "payer_bank": "Meridian Bank",
    "reference": "INV 2211 BOILER",
    "end_to_end_id": "MER26092214204811"
  }
]
