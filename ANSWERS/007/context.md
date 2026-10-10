# Supplied case 007

## history.md

# Sharing a returned deposit — history

Total events: 4

The opening internal note is a snapshot available to the servicing agent at the time of contact; any earlier dates within it refer to records, not to the creation time of this note. Events on the same day without individual timestamps follow the source conversation order.

<a id="event-001"></a>
## 2026-09-22 (individual event time not recorded) — event 001

- **Channel:** Internal account view
- **From:** Harrow & Vale Bank plc (case record)
- **To:** Servicing agent (Harrow & Vale Bank plc)

Customer: **Miya Yagisawa** — personal current account. Balance before today: £412.30.
| Date | Event |
|---|---|
| 22 Sep 10:05 | Credit +£1,260.00 from "OAKFIELD PM CLIENT A/C", ref "DEP RETURN 7 ISFIELD RD" |

Customer's request (below) with the amounts she wants to send. CoP results for the three new payees:
| Payee | CoP |
|---|---|
| Salvatore Russell | Match |
| Jack Elson | Match |
| Emerald Creagh | **No match** — account name held is "E CREAGH-DOYLE" |

<a id="event-002"></a>
## 2026-09-22 (individual event time not recorded) — event 002

- **Channel:** In-app chat (personal banking)
- **From:** Customer
- **To:** Servicing agent (Harrow & Vale Bank plc)

Our deposit came back to my account today because I was the lead tenant. Can you split it and send my flatmates their shares? Deposit was £1,800, £450 each. Landlord kept £540 for damage, cleaning and a plumbing thing that was Salvatore's fault. So: Salvatore £247.50, Jack £375.00, Emerald £337.50, and I keep my £337.50. Details attached. Can you send them today, Jack's being a pain about it.
`[Attachment: deposit_split.csv]`

<a id="event-003"></a>
## 2026-09-22 (individual event time not recorded) — event 003

- **Channel:** In-app chat (personal banking)
- **From:** Servicing agent (Harrow & Vale Bank plc)
- **To:** Customer / caller

I can help you get these paid. Let me check the amounts against what came in.

<a id="event-004"></a>
## 2026-09-22 (individual event time not recorded) — event 004

- **Channel:** In-app chat (personal banking)
- **From:** Customer
- **To:** Servicing agent (Harrow & Vale Bank plc)

It's all worked out, everyone agreed the deductions in writing. Just needs sending.


## request.md

# Sharing a returned deposit

## Case details

- **Source role:** Bank customer
- **Status:** Requires decision
- **Created:** 2026-09-22 (day precision)
- **Updated:** 2026-09-22 (day precision)
- **Bank:** Harrow & Vale Bank plc
- **Channel:** In-app chat (personal banking)

## Initial request

Our deposit came back to my account today because I was the lead tenant. Can you split it and send my flatmates their shares? Deposit was £1,800, £450 each. Landlord kept £540 for damage, cleaning and a plumbing thing that was Salvatore's fault. So: Salvatore £247.50, Jack £375.00, Emerald £337.50, and I keep my £337.50. Details attached. Can you send them today, Jack's being a pain about it.

## History

[Read the complete event history](history.md).

## Attachments

- [deposit return statement from the agency (PDF)](attachments/agency_deposit_statement.pdf)
- [Confirmation of Payee results for the three payees](attachments/cop_results.json)
- [the customer's split as she sent it](attachments/deposit_split.csv)


## attachments/agency_deposit_statement.pdf

Oakfield Property Management Ltd
lettings@oakfieldpm.example  |  
Ms M. Yagisawa (lead tenant)
on behalf of: S. Russell, J. Elson, E. Creagh
22 September 2026
Ref: DEP/7ISF/2026
Deposit return statement - 7 Isfield Road, Lewes
Tenancy ended 31 August 2026. Deposit held: £1,800.00 (£450.00 per tenant). Deductions agreed in writing
by all four tenants on 18 September 2026.
Item Amount
Ground Effects - garden reinstatement (shared) £300.00
Plumbing - blocked ensuite (S. Russell only) £90.00
End-of-tenancy clean (shared; landlord pays remaining £50) £150.00
Total deductions £540.00
Returned to lead tenant account 22/09/2026 £1,260.00
Per-tenant shares after deductions: M. Yagisawa £337.50; S. Russell £247.50; J. Elson £337.50; E. Creagh £337.50.
Somma Patel, Lettings Manager
14 Example Way, Lewes ZZ1 1ZZ
01632 960142
Oakfield Property Management Ltd - synthetic training document

## attachments/cop_results.json

[
  {
    "payee": "Salvatore Russell",
    "sort_code": "SYN-SC-07-2",
    "account_number": "SYN-ACCT-07-1",
    "matched": true
  },
  {
    "payee": "Jack Elson",
    "sort_code": "SYN-SC-07-3",
    "account_number": "SYN-ACCT-07-3",
    "matched": true
  },
  {
    "payee": "Emerald Creagh",
    "sort_code": "SYN-SC-07-1",
    "account_number": "SYN-ACCT-07-2",
    "matched": false,
    "reason_code": "ANNM",
    "name_at_bank": "E CREAGH-DOYLE"
  }
]


## attachments/deposit_split.csv

payee,sort_code,account,amount,note
Salvatore Russell,SYN-SC-07-2,SYN-ACCT-07-1,247.50,450 - 75 (Ground Effects) - 37.50 (cleaning) - 90 (plumbing)
Jack Elson,SYN-SC-07-3,SYN-ACCT-07-3,375.00,450 - 75 - 37.50
Emerald Creagh,SYN-SC-07-1,SYN-ACCT-07-2,337.50,450 - 75 - 37.50
Miya (me - keep),,,337.50,450 - 75 - 37.50
