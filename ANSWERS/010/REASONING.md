## 1. Situation and history

The full input is in the saved `context.md`. Everything below happened on 2026-09-22, with no individual times recorded.

- **request.md:** Case opened on the business banking phone line. Source role is **Third party**. There are **no attachments**.
- **event-002 (caller's report):** The caller says he is a subcontractor for Haldane Homes. He makes three requests:
  - which invoice a £90 payment received "on the 1st" relates to
  - whether Haldane Homes has the money to pay his overdue £1,400 invoice
  - a direct number for whoever looks after their account at the bank
- **event-003:** The agent asks whether he holds an account with Harrow & Vale.
- **event-004 (caller's report):** He says no, he banks with Meridian, and adds: "it's your customer that paid me, so you must be able to see it."
- **event-001 (internal case record, a snapshot for the agent):** Records what the caller said: he identifies as Dave Tilley of Tilley's Maintenance, not an H&V customer, and says he received £90.00 on 1 Sep from "HALDANE HOMES LTD" with a numeric reference. It also records internal account information:
  - Haldane Homes Ltd is an H&V business customer.
  - Its account shows a £90.00 Faster Payment to payee "TILLEYS MAINTENANCE" on 1 Sep, plus other payments to that payee in Aug/Sep.

**What the caller said vs what the bank's records show:** The caller's name, business, subcontractor relationship and the £1,400 overdue invoice all come only from what he said (event-001, event-002, event-004). None of it is verified. The facts about Haldane Homes's account come from the bank's own internal view (event-001). These are confidential to the account holder and are not available for disclosure to him.

## 2. Evidence and gaps

- **Authority is not established.** The caller confirms he is not a customer (event-004). There is no authority document from Haldane Homes Ltd (request.md: no attachments). The plan lists this authority as missing and deliberately does not ask for it, because the caller can get what he needs from Haldane Homes directly.
- **Identity is unverified.** "Dave Tilley, Tilley's Maintenance" is self-declared. Even if it were verified, being the payee would not give him rights over the payer's account information.
- **The £1,400 invoice** is only the caller's claim (event-002). Nothing in the context corroborates it, and the plan does not need it to.
- **The caller's argument at event-004** — that the bank can see the payment — is correct (event-001). But being able to see it does not make it permissible to disclose it.
- **What cannot be established from this case:** which invoice the £90 relates to (only the payer can say, through a remittance advice), and anything about Haldane Homes's ability to pay. The reference string is not interpreted.

## 3. Why this plan

**Step s1 – hold / decline the disclosure**
- *Explanation:* The caller has confirmed he is not a customer, and nothing shows he has authority from the account holder. All three requests would disclose another customer's confidential account information or staff contact details.
- *Evidence:* event-001, event-002, event-004, request.md.
- *Criterion:* Hold the unsafe disclosure where privacy or authority is not established, and limit any disclosure to established authority.
- *Rule source:* `skill:privacy-documents`. This is a skill handling rule. It is not a bank policy document supplied in the context, and the plan cites no specific legal clause, so none is claimed here.
- *Scope:* The refusal also covers whether Haldane Homes banks with H&V at all. Confirming that would itself disclose a customer relationship.

**Step s2 – reply to the caller (requires s1)**
- *Explanation:* The caller should get a clear, polite answer that refuses the disclosure and points him to the right people: the payer for invoice matching and the overdue invoice, and his own bank for how the payment was credited.
- *Evidence:* event-002, event-004.
- *Criterion:* When declining a privacy-restricted disclosure, still provide useful general information and a supported route.
- *Rule source:* `general:safety`.

**Order:** The decision to decline (s1) fixes the limits on what the reply (s2) may say, so s2 depends on s1.

**Safety flags:** privacy and identity_authority. No escalation triggers are defined (`escalate_if` is empty).

## 4. Execution boundaries

Both steps are proposed. Neither has been carried out. The plan ends with the declined disclosure and the reply. It does not request authority from Haldane Homes, open any further case, refer the matter internally or follow up. Anything beyond these two steps would need a fresh decision.

## 5. Expected result and limits

**Expected disposition:** refused.

**What the steps could achieve:** If carried out, the caller gets a polite refusal and three routes:
- Haldane Homes' accounts team, for a remittance advice and the overdue invoice
- Haldane Homes, for where the £1,400 invoice stands
- Meridian, for how the payment appears on his own account

**What stays unconfirmed:** which invoice the £90 covers, and whether the £1,400 invoice will be paid. The bank will not and cannot answer either.

**The reply must state:**
- H&V cannot discuss or confirm any details of another party's account, payments, balance or bank relationship with someone not authorised on that account.
- He should ask Haldane Homes directly for a remittance advice and take up the overdue invoice with them.
- Meridian can help with how the incoming payment appears on his account.

**The reply must not:**
- confirm or deny that Haldane Homes Ltd is an H&V customer
- confirm, describe or match to an invoice any payment in its account, including the £90.00 payment or the other Aug/Sep payments to TILLEYS MAINTENANCE
- indicate its balance, available funds or ability to pay
- give any staff name, number or contact details
- interpret or decode the payment reference
