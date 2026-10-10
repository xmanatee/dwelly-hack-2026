# Decision memo: case 017, 29 Sep reconciliation gap

The full input is in the saved `context.md`. Below, event IDs (`event-00x`) and attachment filenames refer to that file.

## 1. Situation and history

**Customer report (unverified claims):**
- **event-002 / request (30 Sep 2026, Business banking chat):** The bookkeeper, Violetta, says Bright Sparks Electrical Ltd is "£1,750 out" on its 29 Sep reconciliation. Her download shows £30,078.94 of credits, but her closing figure only works if credits were £31,828.94. She suspects a payment "has been lost" and asks for an investigation.
- **event-003:** The agent said they would compare the export with the account's full-day activity.
- **event-004:** Violetta passes on her director's wish to log a formal missing-funds complaint "if it isn't found today".
- **`attachments/bookkeeper_reconciliation_2026-09-29.csv`:** Her working:
  - Opening balance: £32,113.84
  - Plus credits: £30,078.94
  - Less supplier batch: £8,415.30
  - Expected closing: £53,777.48
  - Closing on screen: £55,527.48
  - Difference: £1,750.00
  - Her note says: "Export taken 13:15; balance noted from Business Online dashboard later that afternoon."

**Bank records:**
- **event-001 (internal account view):**
  - The CSV export was requested by user violetta.k at 13:15:02 on 29 Sep.
  - Two credits arrived after 13:15: £1,750.00 at 14:02 (K WHITTLE, INV 4471) and £120.00 at 16:41 (A ROSS, INV 4480 PART).
  - The quoted closing figure matches the running balance between 14:02 and 16:41.
  - The same pattern happened on 28 Sep: £1,900.00 arrived at 18:10, after a 13:20 export.
- **`attachments/export_2026-09-29_1315.csv`:**
  - Exported at 2026-09-29T13:15:02.
  - Four credits: £875.00, £1,200.00, £27,343.94 and £660.00.
  - Supplier batch debit of £8,415.30 at 11:05:12.
  - Running balance afterwards: £53,777.48.
- **`attachments/full_day_2026-09-29.csv` (bank's end-of-day view):** The same entries, plus:
  - P LEWIS £1,900.00 at 2026-09-28T18:10:22 (running balance £32,113.84)
  - K WHITTLE £1,750.00 at 14:02:47 (running balance £55,527.48)
  - A ROSS £120.00 at 16:41:09 (running balance £55,647.48)

## 2. Evidence and gaps

**Arithmetic check (from the attachments):**
- Credits in the export: 875.00 + 1,200.00 + 27,343.94 + 660.00 = **£30,078.94**. This matches the bookkeeper's line 2.
- Opening balance: £32,113.84 + £30,078.94 − £8,415.30 = **£53,777.48**. This matches the export's last running balance and her expected closing.
- Adding the £1,750.00 credit gives **£55,527.48**, the figure she read from the screen. Credits would then be £31,828.94, exactly the total she said was needed (event-002).
- Adding the £120.00 credit gives a full-day closing of **£55,647.48** and full-day credits of **£31,948.94**.

**What this shows:** The "missing" £1,750.00 is booked on the account (`full_day_2026-09-29.csv`, event-001). It was booked after the export's timestamp, which is why it is not in the export.

**Gaps and uncertainties:**
- **Exact time of the screen reading.** It isn't recorded. "Between 14:02 and 16:41" is worked out from the balance match and her "later that afternoon" note. It is a strong inference, not a logged time.
- **28 Sep export.** The 13:20 export time comes only from event-001. No 28 Sep export file was supplied. The bank file does confirm that the P LEWIS £1,900.00 credit at 18:10:22 is included in her £32,113.84 opening figure. Whether that credit is in her ledger is for her to check, which is why the reply asks her to.
- **Director's wishes.** The plan records as missing whether the director still wants a complaint now that the funds are located. This is unresolved.
- **Payer's side.** No information was supplied about the payers beyond the booked credits.

## 3. Why this plan

**Step s1 (reply to customer)** is the only action.
- **Explanation:** The full-day record shows the £1,750.00 booked at 14:02:47, after the 13:15:02 export. The screen balance equals the running balance after that credit. So the gap is a timing mismatch, not a missing payment. The complaint request depended on the funds not being found. The reply therefore explains that no complaint has been logged, and still leaves the complaint open to the customer without conditions.
- **Evidence cited by the plan:** event-001, event-002, event-004, `export_2026-09-29_1315.csv`, `full_day_2026-09-29.csv` and `bookkeeper_reconciliation_2026-09-29.csv`.
- **Decision criterion:**
  - Use the authoritative supplied status directly.
  - Identify the exact transaction by amount, time, counterparty and reference.
  - State only what the record proves.
  - Do not make registering a complaint depend on the customer giving up the query.
- **Rule source:** `skill:payments`. This is a skill handling rule. No bank complaint-handling policy or legal obligation was supplied, and none is relied on here.

**Why no other actions:**
- No investigation, trace or complaint registration is proposed, because the record already accounts for the credit.
- Identity and authority are marked as established, and there are no safety flags.
- Registering a complaint without the director's renewed instruction would go against the conditional request in event-004. Refusing one would breach the criterion above. Offering to register it on request avoids both.

**Why include the extra details:** The reply also mentions the later £120.00 credit and the 28 Sep pattern. This lets the bookkeeper reconcile the full day correctly and check her opening figure, not just explain the £1,750.00.

## 4. Execution boundaries

- Nothing has been executed. Step s1 is a proposed reply only. It has no dependencies or conditions (`requires: []`, `condition: null`) and no escalation triggers.
- The plan ends with this reply. If the director asks for a complaint afterwards, that is a new request needing a fresh decision. This plan does not set up that branch or any other.

## 5. Expected result and limits

**What s1 can achieve:** If sent, it should let the bookkeeper close the 29 Sep reconciliation at £55,647.48 and check the 28 Sep P LEWIS credit. It also tells the director, without conditions, that a complaint can still be made.

**What remains unconfirmed:**
- Whether the director wants a complaint.
- Whether the 28 Sep credit is in the customer's ledger.
- The exact time of the screen reading.

**The message must state:**
- The £1,750.00 is from K WHITTLE (INV 4471), booked at 14:02:47 on 29 Sep, after the 13:15:02 export.
- The export's four credits total £30,078.94 and match the bank's records. £55,527.48 is the balance after the 14:02 credit.
- A further £120.00 from A ROSS (INV 4480 PART) was booked at 16:41:09. The full-day closing is £55,647.48 and full-day credits total £31,948.94.
- The 28 Sep £1,900.00 credit from P LEWIS (INV 4461) landed at 18:10:22, after the 13:20 export, and should be checked in the ledger.
- No complaint has been logged because the funds were found. One will be registered if the director wants it.

**The message must not:**
- Say a payment is missing, lost or under investigation.
- Suggest a bank or statement error.
- Claim a complaint was registered or give a complaint reference.
- Make a complaint depend on the customer accepting the explanation.
- Assert anything about the payers beyond the booked credits.
- Promise any outcome, timescale or compensation.
