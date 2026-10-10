# Supplied case 001

## history.md

# Incoming payment under review — history

Total events: 6

The opening internal note is a snapshot available to the servicing agent at the time of contact; any earlier dates within it refer to records, not to the creation time of this note. Events on the same day without individual timestamps follow the source conversation order.

<a id="event-001"></a>
## 2026-09-24 (individual event time not recorded) — event 001

- **Channel:** Internal account view
- **From:** Harrow & Vale Bank plc (case record)
- **To:** Servicing agent (Harrow & Vale Bank plc)

Customer: **Marcus Bell** — personal current account, 6 years with the bank, no previous fraud markers.
| Date | Event |
|---|---|
| 21 Sep 14:10 | Credit +£2,600.00, Faster Payment from "L FARRELL" (Meridian Bank), ref "VAN" |
| 21 Sep 16:40 | Debit −£1,850.00 to "BARCLAYCARD" (his own card, payee on file since 2022) |
| 23 Sep 17:55 | **Inbound funds-recovery request** from Meridian: their customer reports the £2,600 as an authorised push payment scam ("vehicle not delivered"). Bank policy: place a hold on the disputed amount still available, respond to the sending bank within 2 working days |
| 23 Sep 17:56 | Hold applied: £750.00 (all available funds); account balance £750.00, hold £750.00 |

Customer's contact history: none in the last 12 months. No other inbound payments from unknown parties in the last 90 days.

<a id="event-002"></a>
## 2026-09-24 (individual event time not recorded) — event 002

- **Channel:** Phone (personal banking)
- **From:** Customer
- **To:** Servicing agent (Harrow & Vale Bank plc)

[ID&V passed] I've got no access to my money. It says £750 is held and I can't pay my rent tomorrow. What's going on?

<a id="event-003"></a>
## 2026-09-24 (individual event time not recorded) — event 003

- **Channel:** Phone (personal banking)
- **From:** Servicing agent (Harrow & Vale Bank plc)
- **To:** Customer / caller

I can see a hold was placed yesterday evening. I need to ask you about a payment you received on the 21st — £2,600 from an L Farrell.

<a id="event-004"></a>
## 2026-09-24 (individual event time not recorded) — event 004

- **Channel:** Phone (personal banking)
- **From:** Customer
- **To:** Servicing agent (Harrow & Vale Bank plc)

That's the van. I sold my old Transit on a marketplace site, she came and picked it up Monday, paid me by transfer while she was standing in my drive. I've got the messages, the listing, the V5 handover — all of it. I used most of it to pay off my credit card. Why is that your business?

<a id="event-005"></a>
## 2026-09-24 (individual event time not recorded) — event 005

- **Channel:** Phone (personal banking)
- **From:** Servicing agent (Harrow & Vale Bank plc)
- **To:** Customer / caller

Thank you — that context matters. Let me explain what has happened and what I need from you.

<a id="event-006"></a>
## 2026-09-24 (individual event time not recorded) — event 006

- **Channel:** Phone (personal banking)
- **From:** Customer
- **To:** Servicing agent (Harrow & Vale Bank plc)

You need to release my money is what you need to do. My rent's £900 and it's due tomorrow.


## request.md

# Incoming payment under review

## Case details

- **Source role:** Bank customer
- **Status:** Requires decision
- **Created:** 2026-09-24 (day precision)
- **Updated:** 2026-09-24 (day precision)
- **Bank:** Harrow & Vale Bank plc
- **Channel:** Phone (personal banking)
- **Contact start:** 09:20 local UK time (individual message times not recorded)

## Initial request

I've got no access to my money. It says £750 is held and I can't pay my rent tomorrow. What's going on?

## History

[Read the complete event history](history.md).

## Attachments

- [internal hold notice on the account](attachments/account_hold_notice.txt)
- [marketplace listing exported by the customer](attachments/customer_evidence_listing.txt)
- [marketplace chat with the buyer, exported by the customer](attachments/customer_evidence_messages.txt)
- [interbank recovery request as received from Meridian](attachments/funds_recovery_request_MERIDIAN.txt)


## attachments/account_hold_notice.txt

H&V internal - account hold notice
Account: Marcus Bell, SYN-SC-01-1 / SYN-ACCT-01-1
Hold applied: 2026-09-23 17:56 by system (inbound recovery request MER-FR-2026-081734)
Amount held: GBP 750.00 (all available funds). Disputed amount: GBP 2,600.00. Already spent before request: GBP 1,850.00 (2026-09-21 16:40 to BARCLAYCARD, payee on file since 2022).
Customer contact history (12 months): none. Fraud markers: none. Other inbound credits from unknown parties (90 days): none.


## attachments/customer_evidence_listing.txt

[Listing exported by customer from marketplace app]
Title: Ford Transit Custom 2017, 2.0 TDCi, 98k miles, MOT till Feb 2027
Price: £2,600  |  Listed: 12 Sep 2026  |  Seller: Marcus B. (member since 2019, 14 reviews, 4.9)
Location: Reading  |  Collection only
Description: Selling my work van, moving to a car. Two owners, full service history, new brake pads June 2026. Small dent rear door (photos). V5C present, buyer welcome to inspect and test drive. No delivery, collection only.
Status: SOLD (marked sold 21 Sep 2026)


## attachments/customer_evidence_messages.txt

[Marketplace chat exported by customer - buyer account "Lou F."]
19 Sep 20:14  Lou F.: Hi is the Transit still available? Can I come see it Monday?
19 Sep 20:31  Marcus B.: Yes still here. Monday 2pm ok? RG1 4TP, I'll send the exact address once you confirm.
19 Sep 20:35  Lou F.: Perfect. Will bring my partner to drive it back.
21 Sep 13:52  Lou F.: Here, parked outside no 14
21 Sep 14:06  Lou F.: Happy with it, sending the money now by bank transfer, ref VAN
21 Sep 14:11  Marcus B.: Got it, thanks. V5C green slip filled in, you've got the keys, both sets. Safe drive.
21 Sep 14:12  Lou F.: Cheers mate


## attachments/funds_recovery_request_MERIDIAN.txt

INTERBANK FUNDS RECOVERY REQUEST (APP scam - Best Practice Standards)
Received: 2026-09-23 17:55:12 BST
From: Meridian Bank plc, Fraud Operations   To: Harrow & Vale Bank plc, Fraud Operations
Case ref (sending bank): MER-FR-2026-081734
Original payment: Faster Payment, 2026-09-21 14:10:07, GBP 2,600.00
Payer: L FARRELL (Meridian SYN-SC-01-2 / SYN-ACCT-01-2)   Payee: sort SYN-SC-01-1 acct SYN-ACCT-01-1 (H&V)   Reference: VAN
Reported by payer: 2026-09-23 16:40. Category: Purchase scam - goods not received (vehicle).
Payer statement (summary): "Paid for a Transit van seen online. Seller said it would be delivered Tuesday. No van, seller not answering."
Request: hold any remaining funds and return to Meridian. Please respond within 2 working days.
Note: no police reference supplied. No previous reports against payee account.
