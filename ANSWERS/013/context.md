# Supplied case 013

## history.md

# Rent collection and an unpaid notice — history

Total events: 3

The opening internal note is a snapshot available to the servicing agent at the time of contact; any earlier dates within it refer to records, not to the creation time of this note. Events on the same day without individual timestamps follow the source conversation order.

<a id="event-001"></a>
## 2026-09-23 (individual event time not recorded) — event 001

- **Channel:** Internal account view
- **From:** Harrow & Vale Bank plc (case record)
- **To:** Servicing agent (Harrow & Vale Bank plc)

Customer: **Rina Patel** — personal current account.
Direct Debit: H&V COLLECT / NORTHGATE LETTINGS, £750 monthly.
| Date | Event |
|---|---|
| 18 Sep | Collection £750 presented — **returned unpaid, "refer to payer"** (available balance £710.40) |
| 19 Sep | Automated letter: "A Direct Debit for £750.00 could not be paid" |
| 21 Sep | Collection £750 **re-presented by originator — paid** (salary credited 20 Sep) |

No unpaid-item fee is charged by H&V. No further collection is scheduled before 18 Oct.

<a id="event-002"></a>
## 2026-09-23 (individual event time not recorded) — event 002

- **Channel:** In-app chat (personal banking)
- **From:** Customer
- **To:** Servicing agent (Harrow & Vale Bank plc)

I got a letter saying my rent direct debit failed on the 18th. But I can see £750 went out to the agency on the 21st. The agency have texted me that the payment "failed" and I should pay manually today so I'm not in arrears. I don't want to be in arrears but I also don't want to pay twice. What's going on?

<a id="event-003"></a>
## 2026-09-23 (individual event time not recorded) — event 003

- **Channel:** In-app chat (personal banking)
- **From:** Servicing agent (Harrow & Vale Bank plc)
- **To:** Customer / caller

Let me check both dates on the mandate.


## request.md

# Rent collection and an unpaid notice

## Case details

- **Source role:** Bank customer
- **Status:** Requires decision
- **Created:** 2026-09-23 (day precision)
- **Updated:** 2026-09-23 (day precision)
- **Bank:** Harrow & Vale Bank plc
- **Channel:** In-app chat (personal banking)

## Initial request

I got a letter saying my rent direct debit failed on the 18th. But I can see £750 went out to the agency on the 21st. The agency have texted me that the payment "failed" and I should pay manually today so I'm not in arrears. I don't want to be in arrears but I also don't want to pay twice. What's going on?

## History

[Read the complete event history](history.md).

## Attachments

- [screenshot of the agency's text message (image)](attachments/agency_text_screenshot.png)
- [statement extract](attachments/statement_extract.csv)
- [the letter the bank sent (PDF)](attachments/unpaid_dd_letter_2026-09-19.pdf)


## attachments/agency_text_screenshot.png

[Attachment unread: unsupported .png format; no OCR performed.]

## attachments/agency_text_screenshot.png.ocr.txt

# Local OCR of agency_text_screenshot.png

Machine transcription; the original image is preserved.

< Northgate Lettings

Hi Rina, our system shows your rent
Direct Debit for September FAILED.
To avoid arrears please make a
manual payment of £750 today to
our client account. Ref
NL-9LIME-0442. Thanks, Northgate.

Tue 22 Sep, 16:20


## attachments/statement_extract.csv

date,type,description,amount,balance
2026-09-18,DD RETURNED,H&V COLLECT / NORTHGATE LETTINGS  NL-9LIME-0442  (refer to payer),0.00,710.40
2026-09-20,CR,SALARY  BRIGHTON & CO LLP,2145.00,2855.40
2026-09-21,DD,H&V COLLECT / NORTHGATE LETTINGS  NL-9LIME-0442  (re-presentation),-750.00,2105.40


## attachments/unpaid_dd_letter_2026-09-19.pdf

Harrow & Vale Bank plc
Ms Rina Patel 19 September 2026
Account ending 6621
A Direct Debit could not be paid
We tried to pay a Direct Debit from your account but there was not enough money available.
Direct Debit to: NORTHGATE LETTINGS LTD (via H&V Collect) Amount: £750.00 Date presented: 18
September 2026
We have not charged a fee for this. The organisation may try to collect the payment again, or contact you
about it. If you have any questions about what you owe, please contact the organisation directly.
If you'd like help avoiding this in future, you can set up a low-balance alert in the app.
Customer Services, Example PO Box, Leeds ZZ1 1ZZ
harrowvale.example  |  01632 960123
Flat 3, 9 Example Grove
Leeds ZZ2 2ZZ
Harrow & Vale Bank plc is fictional; this is a synthetic training document.
