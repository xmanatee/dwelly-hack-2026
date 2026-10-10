---
name: payments
description: Transfers, incoming payments, duplicates, returns, international payments, amount or status disputes.
---

# Payments

Identify the exact transaction by available reference, amount, currency, date and parties; similar transfers are not automatically duplicates. Distinguish authorisation, debit, release/sent, settlement and recipient credit. State only the stage the supplied record proves. An incoming payer claim is not evidence of a booked credit.

Use a supplied authoritative status directly. Request a named journal lookup only for a material gap. A recall/return request is not a completed return; a refund record is not proof of a separate merchant or recipient-bank action. Give supported failure reasons without guessing a sanctions, fraud or balance cause. Do not promise arrival times absent an applicable commitment.

External guidance: Open Banking supplies separate account-information and payment-initiation specifications. The Ombudsman distinguishes fraud from other disputed transactions and considers evidence, account terms and rules in force at the time. Our status and evidence distinctions above are engineering rules derived from the case histories, not a claim that their fictional states implement that API.

## Provenance

Reviewed 2026-10-10. UK-oriented guidance; apply only where jurisdiction, event date and scope fit. Case facts and bank procedures must come from supplied evidence.

- [Open Banking Read/Write API specifications](https://github.com/OpenBankingUK/read-write-api-specs) — API/schema reference; does not define a bank’s customer-service policy.
- [Financial Ombudsman: disputed transactions](https://www.financial-ombudsman.org.uk/consumers/complaints-can-help/banking-and-payments/disputed-transactions) — UK complaints; consider the rules and account terms applicable at the event date.
