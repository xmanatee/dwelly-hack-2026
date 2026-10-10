# Supplied case 005

## history.md

# Direct Debit after move-out — history

Total events: 4

The opening internal note is a snapshot available to the servicing agent at the time of contact; any earlier dates within it refer to records, not to the creation time of this note. Events on the same day without individual timestamps follow the source conversation order.

<a id="event-001"></a>
## 2026-09-25 (individual event time not recorded) — event 001

- **Channel:** Internal account view
- **From:** Harrow & Vale Bank plc (case record)
- **To:** Servicing agent (Harrow & Vale Bank plc)

Customer: **Gabriela Petrova** — personal current account, no arranged overdraft.
Direct Debit mandate: H&V COLLECT / OAKFIELD PM, active since Feb 2025, monthly.
| Date | Amount | Status |
|---|---|---|
| 24 Aug | −£875.00 | Collected |
| 23 Sep | −£875.00 | Collected — account went £412 overdrawn; £6.50 unarranged overdraft fee applied 24 Sep |
| **28 Sep (Mon)** | **−£2,525.00** | **Scheduled — collection instruction received from originator 24 Sep** |

On 25 Sep a £1,019.40 transfer from the customer's savings posted; available balance is now £600.00.

The customer states her tenancy at 78 Coombe Road ended on **31 Aug 2026**. The bank cannot see whether advance notices were sent for the Sep collections.

<a id="event-002"></a>
## 2026-09-25 (individual event time not recorded) — event 002

- **Channel:** Phone (personal banking)
- **From:** Customer
- **To:** Servicing agent (Harrow & Vale Bank plc)

[ID&V passed] I moved out of my flat at the end of August. The agency took £875 on the 23rd, which has put me overdrawn, and I've just seen there's another one for £2,525 going out on Monday! I rang the agency and they said it's "already been submitted, they can't cancel it their side" and I should call you. I've got £600 in the account. What is this?

<a id="event-003"></a>
## 2026-09-25 (individual event time not recorded) — event 003

- **Channel:** Phone (personal banking)
- **From:** Servicing agent (Harrow & Vale Bank plc)
- **To:** Customer / caller

I'm sorry, that sounds really stressful. Let me look at the mandate.

<a id="event-004"></a>
## 2026-09-25 (individual event time not recorded) — event 004

- **Channel:** Phone (personal banking)
- **From:** Customer
- **To:** Servicing agent (Harrow & Vale Bank plc)

I want all of it refunded — the August one, the September one, and Monday's stopped. And I want the overdraft fee back, it's not my fault.


## request.md

# Direct Debit after move-out

## Case details

- **Source role:** Bank customer
- **Status:** Requires decision
- **Created:** 2026-09-25 (day precision)
- **Updated:** 2026-09-25 (day precision)
- **Bank:** Harrow & Vale Bank plc
- **Channel:** Phone (personal banking)
- **Contact start:** 11:30 local UK time (individual message times not recorded)

## Initial request

I moved out of my flat at the end of August. The agency took £875 on the 23rd, which has put me overdrawn, and I've just seen there's another one for £2,525 going out on Monday! I rang the agency and they said it's "already been submitted, they can't cancel it their side" and I should call you. I've got £600 in the account. What is this?

## History

[Read the complete event history](history.md).

## Attachments

- [agency email confirming the tenancy end date (forwarded by customer)](attachments/agency_move_out_confirmation.eml)
- [the scheduled collection instruction received from the originator](attachments/incoming_dd_instruction.json)
- [statement extract](attachments/statement_extract.csv)


## attachments/agency_move_out_confirmation.eml

From: Oakfield PM <lettings@oakfieldpm.example>
To: g.petrova@example.net
Subject: 78 Coombe Road - end of tenancy confirmed
Date: Tue, 01 Sep 2026 10:05:00 +0100
MIME-Version: 1.0
Content-Type: text/plain; charset=utf-8

Hi Gabriela,

Thanks for handing the keys back yesterday. We confirm your tenancy at 78 Coombe Road ended on 31 August 2026. The check-out report will follow within 10 working days and your deposit will be dealt with after that.

Kind regards,
Somma
Oakfield Property Management


## attachments/incoming_dd_instruction.json

{
  "originator": "OAKFIELD PROPERTY MANAGEMENT LTD",
  "service_user_number": "H&V COLLECT 771902",
  "mandate_ref": "OPM-78COOMBE-3312",
  "payer_account": "SYN-SC-05-1 / SYN-ACCT-05-1",
  "amount": 2525.0,
  "collection_date": "2026-09-28",
  "received_by_bank": "2026-09-24T02:10:44Z",
  "status": "scheduled",
  "narrative_from_originator": "FINAL ACCOUNT 78 COOMBE RD"
}


## attachments/statement_extract.csv

date,type,description,amount,balance
2026-08-24,DD,H&V COLLECT / OAKFIELD PM  OPM-78COOMBE-3312,-875.00,1204.60
2026-09-01,DB,NEW TENANCY RENT,-1052.50,152.10
2026-09-19,CR,WAGES ELMSTEAD CARE LTD,1310.00,1462.10
2026-09-21,DB,TRANSFER TO CUSTOMER SAVINGS,-1000.00,462.10
2026-09-23,DD,H&V COLLECT / OAKFIELD PM  OPM-78COOMBE-3312,-875.00,-412.90
2026-09-24,FEE,UNARRANGED OVERDRAFT DAILY FEE,-6.50,-419.40
2026-09-25,CR,TRANSFER FROM CUSTOMER SAVINGS,1019.40,600.00
