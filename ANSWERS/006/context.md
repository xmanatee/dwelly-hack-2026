# Supplied case 006

## history.md

# Unexpected incoming payment — history

Total events: 4

The opening internal note is a snapshot available to the servicing agent at the time of contact; any earlier dates within it refer to records, not to the creation time of this note. Events on the same day without individual timestamps follow the source conversation order.

<a id="event-001"></a>
## 2026-09-28 (individual event time not recorded) — event 001

- **Channel:** Internal account view
- **From:** Harrow & Vale Bank plc (case record)
- **To:** Servicing agent (Harrow & Vale Bank plc)

Customer: **Aisha Khan**, 20 — personal current account (student), opened 2024. Typical activity: student loan credits, part-time wages, small card spend.
| Date | Event |
|---|---|
| 26 Sep 22:14 | Credit +£750.00, Faster Payment from "R JAMES" (Meridian Bank), ref "RENT" |

No inbound funds-recovery request has been received from Meridian. The customer has forwarded a text message she received on 27 Sep from an unknown mobile number: *"Hi, this is Ryan, I sent £750 to your account by mistake last night, it was meant for my landlord. Please can you send it back to my other account, it's easier: SYN-SC-06-3, SYN-ACCT-06-1, R James. Really appreciate it, I'm in a bind. Thanks!!"*

CoP check on the details in the text: **No match** — account name held is not "R James".

<a id="event-002"></a>
## 2026-09-28 (individual event time not recorded) — event 002

- **Channel:** In-app chat (personal banking)
- **From:** Customer
- **To:** Servicing agent (Harrow & Vale Bank plc)

Hi, someone paid £750 into my account by accident on Saturday and they've texted asking me to send it back. Can I just do that now? I feel bad for them, they said it was their rent. I haven't touched it.

<a id="event-003"></a>
## 2026-09-28 (individual event time not recorded) — event 003

- **Channel:** In-app chat (personal banking)
- **From:** Servicing agent (Harrow & Vale Bank plc)
- **To:** Customer / caller

Thank you for checking before sending anything — that's the right call. Let me look at the payment and the details they've given you.

<a id="event-004"></a>
## 2026-09-28 (individual event time not recorded) — event 004

- **Channel:** In-app chat (personal banking)
- **From:** Customer
- **To:** Servicing agent (Harrow & Vale Bank plc)

They gave me a different account to send it to than the one it came from, is that a problem? I just want it gone, it's not my money.


## request.md

# Unexpected incoming payment

## Case details

- **Source role:** Bank customer
- **Status:** Requires decision
- **Created:** 2026-09-28 (day precision)
- **Updated:** 2026-09-28 (day precision)
- **Bank:** Harrow & Vale Bank plc
- **Channel:** In-app chat (personal banking)

## Initial request

Hi, someone paid £750 into my account by accident on Saturday and they've texted asking me to send it back. Can I just do that now? I feel bad for them, they said it was their rent. I haven't touched it.

## History

[Read the complete event history](history.md).

## Attachments

- [Confirmation of Payee result for the details in the text](attachments/cop_check_text_details.json)
- [the inbound Faster Payment message](attachments/inbound_payment_message.json)
- [screenshot of the text message (image)](attachments/sms_screenshot.png)


## attachments/cop_check_text_details.json

{
  "request": {
    "sort_code": "SYN-SC-06-3",
    "account_number": "SYN-ACCT-06-1",
    "name_supplied": "R James",
    "account_type": "personal"
  },
  "response": {
    "matched": false,
    "reason_code": "ANNM",
    "reason": "Account name does not match",
    "checked_at": "2026-09-28T09:52:40Z"
  }
}


## attachments/inbound_payment_message.json

{
  "scheme": "FPS",
  "received": "2026-09-26T22:14:31+01:00",
  "amount": 750.0,
  "currency": "GBP",
  "payer": {
    "name": "R JAMES",
    "sort_code": "SYN-SC-06-2",
    "account_number": "SYN-ACCT-06-2",
    "bank": "Meridian Bank"
  },
  "payee": {
    "sort_code": "SYN-SC-06-1",
    "account_number": "SYN-ACCT-06-3",
    "name": "MISS AISHA KHAN"
  },
  "reference": "RENT",
  "end_to_end_id": "MER26092622143198",
  "recovery_request_received": false
}


## attachments/sms_screenshot.png

[Attachment unread: unsupported .png format; no OCR performed.]

## attachments/sms_screenshot.png.ocr.txt

# Local OCR of sms_screenshot.png

Machine transcription; the original image is preserved.

< +44 7700 900 823

Hi, this is Ryan, | sent £750 to your account by
mistake last night, it was meant for my landlord.
Please can you send it back to my other account,
it's easier: SYN-SC-06-2, SYN-ACCT-06-2. R
James. Thanks!!

Sun 27 Sep, 08:41
