# REASONING — Case 017: Statement balance query (Bright Sparks Electrical Ltd)

Full input is in the saved `context.md`.

## 1. Situation and history

- **event-001 (2026-09-30, internal account view, Harrow & Vale Bank plc):** Authenticated case record for business current account SYN-SC-17-1 / SYN-ACCT-17-1. It records that the CSV export was requested by user `violetta.k` at **13:15:02** on 29 Sep; that two credits booked after that time (+£1,750.00 at 14:02, K WHITTLE, ref "INV 4471"; +£120.00 at 16:41, A ROSS, ref "INV 4480 PART"); that the customer's quoted closing balance matches the running balance between 14:02 and 16:41; and that the same pattern occurred on 28 Sep (+£1,900.00 at 18:10, after a 13:20 export).
- **event-002 (2026-09-30, business banking chat, Violetta — bookkeeper):** Customer report: £1,750 out on 29 Sep balancing; download shows £30,078.94 credits but the closing only works with £31,828.94; asks for a missing-payment investigation and suggests "something's been lost".
- **event-003 (2026-09-30, chat, servicing agent):** Agent states they will compare the export with full-day activity. No results are recorded beyond the attachments.
- **event-004 (2026-09-30, chat, Violetta):** The director wants a formal missing-funds complaint logged **if it isn't found today**.
- **Attachments:** `attachments/bookkeeper_reconciliation_2026-09-29.csv` (customer's working), `attachments/export_2026-09-29_1315.csv` (customer's download), `attachments/full_day_2026-09-29.csv` (bank's end-of-day view).

Contact started 09:40 local UK time on 30 Sep; individual message times are not recorded (request.md).

**Customer report vs authenticated record:** The claim that a credit is "missing" or "lost" (event-002) is a customer assertion. The authenticated records (event-001 and `full_day_2026-09-29.csv`) show every credit booked.

## 2. Evidence and gaps

**Reconciliation of the figures (all from supplied files):**

- `export_2026-09-29_1315.csv` is stamped `exported_at 2026-09-29T13:15:02` and lists four credits (£875.00 J MORGAN INV 4462; £1,200.00 CARDNET SETTLEMENT 2809; £27,343.94 HALDANE HOMES LTD INV 4455 STAGE 2; £660.00 S AHMED INV 4470) totalling **£30,078.94**, and the supplier batch debit of −£8,415.30 at 11:05:12, leaving a running balance of **£53,777.48**. This matches line 4 of the bookkeeper's reconciliation exactly.
- `bookkeeper_reconciliation_2026-09-29.csv` uses a closing balance of **£55,527.48** (line 5) with the note "Export taken 13:15; balance noted from Business Online dashboard later that afternoon". Line 6 difference: £1,750.00.
- `full_day_2026-09-29.csv` shows the same five items as the export, then **£1,750.00 credit, K WHITTLE, INV 4471, 14:02:47, running balance £55,527.48**, then **£120.00 credit, A ROSS, INV 4480 PART, 16:41:09, running balance £55,647.48**.
- The £1,750.00 difference therefore equals, to the penny, the K WHITTLE credit booked 47 minutes after the export; the dashboard balance the bookkeeper used is the running balance between 14:02:47 and 16:41:09. The customer's implied credit figure of £31,828.94 (event-002) = £30,078.94 + £1,750.00, consistent with this.
- The customer's 29 Sep opening balance of £32,113.84 matches the running balance after the £1,900.00 P LEWIS credit (INV 4461) at 18:10:22 on 28 Sep in `full_day_2026-09-29.csv` — the same post-export timing pattern noted in event-001.

**Contradictions:** None between the authenticated records. The only discrepancy is between the customer's inference ("something's been lost") and the records, and it is fully explained by the cut-off timing.

**Gaps (per the plan's `missing`):**
- Whether the director still wants a formal complaint after the explanation — the request in event-004 was conditional on the funds not being found, and that condition is not met on the records. This cannot be assumed either way.
- Exact 30 Sep chat message times are not recorded (only the 09:40 contact start).
- Event-003 records an intention to compare; no execution or output beyond the supplied attachments is recorded. The plan's conclusion rests on the attachments and event-001, not on any recorded agent investigation.

**Identity/authority:** The plan records identity authority as established — Violetta is the bookkeeper, the export was requested under `violetta.k` on the same account (event-001), and the request is for information she already has access to with no account change requested. No safety flags were raised.

## 3. Why this plan

**Step s1 — reply_to_customer (reconciliation explanation).**
- *Explanation (from the plan):* The export, reconciliation and full-day record identify the exact transaction (£1,750.00 K WHITTLE INV 4471 at 14:02:47) and show the difference is a cut-off timing mismatch, not a missing credit; the record also shows a second post-export credit (£120.00 A ROSS) that the customer has not yet accounted for, which is why the true end-of-day close (£55,647.48) is also stated.
- *Evidence cited:* `attachments/export_2026-09-29_1315.csv`, `attachments/bookkeeper_reconciliation_2026-09-29.csv`, `attachments/full_day_2026-09-29.csv`, event-001, event-002.
- *Criterion:* Identify the exact transaction by reference, amount, date and parties and use the supplied authoritative record directly; state only what the record proves.
- *Source:* `skill:payments` — this is a skill handling rule, not a supplied bank policy document or a legal obligation.
- The 28 Sep pattern and the export-after-end-of-day suggestion are included because event-001 records the same pattern and the practical advice follows directly from the evidence; it is advice on the customer's own process, not a promise of any system change.

**Step s2 — ask_customer (complaint confirmation).**
- *Explanation (from the plan):* The complaint request in event-004 was conditional on the funds not being found; the records show them found, so the customer's current wish must be confirmed rather than assumed, while preserving the unconditional right to complain.
- *Evidence cited:* event-004, request.
- *Criterion:* Recognise and route a complaint separately from the operational query; do not make registration conditional on abandoning the dispute; include only acknowledgements actually available.
- *Source:* `skill:complaints-rights` — a skill handling rule. No bank complaints policy or regulatory text was supplied in this case, so no clause is cited.
- No complaint flag is raised at this snapshot because the stated condition ("if it isn't found today") is not met on the records; the plan still offers registration unconditionally and forbids refusing or delaying it on the basis that the explanation resolves the query.

**Order:** s1 precedes s2 so that the customer has the located transaction before being asked whether the conditional complaint request still stands. Neither step has a `requires` dependency or condition; both are messages in the same chat.

**Alternatives considered only as supported by the plan:** Logging the complaint immediately was not selected because the request was expressly conditional and the condition is not met; refusing/closing the complaint route was not selected because the right to complain is unconditional. The plan does not propose any payment trace, recall or investigation because the records show nothing is missing.

## 4. Execution boundaries

- Both actions are **proposed and not executed**. No message has been sent, no complaint has been registered, and no account operation is involved.
- s2 explicitly stops the plan pending the customer's answer: no complaint is to be logged until Violetta confirms the director's wish. If she confirms, registration is the next decision to be taken on that confirmation; the plan does not pre-decide its content or outcome.
- No escalation conditions (`escalate_if` is empty) and no safety flags.
- The plan does not propose any change to Business Online export behaviour, and none should be implied.

## 5. Expected result and limits

**What the steps could achieve:** A complete, evidence-based explanation of the £1,750.00 difference, identification of the second post-export £120.00 credit and the correct end-of-day close (£55,647.48), a practical way to avoid the recurring cut-off mismatch, and a clear, unconditional invitation to confirm whether a formal complaint is still wanted.

**What remains unconfirmed:** Whether the director still wants a complaint registered; whether the customer accepts the explanation. Expected disposition is `completed` for the operational query, subject to the complaint question.

**Constraints preserved (`must_state`):** K WHITTLE £1,750.00 INV 4471 booked 14:02:47 on 29 Sep, not missing; export at 13:15:02 vs dashboard read after 14:02 — different cut-offs; true close £55,647.48 after A ROSS £120.00 INV 4480 PART at 16:41:09; same pattern on 28 Sep (P LEWIS £1,900.00 at 18:10 after 13:20 export) and export-after-end-of-day advice; right to complain available regardless and not conditional on accepting the explanation; no complaint registered yet.

**Constraints preserved (`must_not`):** No statement that funds were lost, misposted or recovered; no claim that a complaint is logged and no promised outcome, redress or timescale; no disclosure beyond Bright Sparks Electrical Ltd's own 28–29 Sep activity; no promise of a Business Online change or system fix; no refusal or delay of complaint registration because the query is resolved.
