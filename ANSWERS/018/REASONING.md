# Decision memo for case 018: rent standing order reduction

The full input is in the saved `context.md`. This memo covers a plan that is only proposed. Nothing has been executed.

## 1. What happened
All four events are dated 2026-09-23, with no individual times recorded.

**Authenticated bank records**
- **event-001** is an internal account view. It shows:
  - Laszlo F. holds a personal current account.
  - There is a standing order of £500.00 on the 1st to HARROW & VALE RE LIME PROPERTY CA, ref "862A BEV RD", in place since Feb 2026.
  - The balance is £96 and there is no overdraft.
  - Salary credits stopped in July. Since August there have been irregular credits of £150–£300 labelled "AGENCY WORK".
- **attachments/account_activity_jul-sep.csv** shows:
  - The standing order paid £500.00 on 1 July, 1 August and 1 September 2026.
  - A final salary credit, "SALARY KP LOGISTICS LTD (FINAL)", of £1,640.00 arrived on 2026-07-25.
  - Agency credits from TEMPFORCE: £210.00 (14 Aug), £285.00 (28 Aug), £150.00 (12 Sep) and £240.00 (22 Sep).
  - The closing balance is £96.00 on 2026-09-22.

**What the customer said** (on the phone, after passing ID&V)
- **event-002 / request.md:** they want the standing order changed to £400 "from next month" and done today. They lost their job in July and are doing agency work. They plan to raise it to £550 later to catch up.
- **event-004:** "I know it's less than the rent. I've told the agency I'll sort it. I just need it changed."

**What the agent said**
- **event-003:** the agent said the standing order can be changed because it's the customer's instruction, then started checking details.

## 2. Evidence and gaps
- **Identity and authority are established.** ID&V was passed on this call (event-002), and the account and standing order are the customer's own (event-001).
- **The job loss is backed by the records.** The customer's account matches the final salary credit and the irregular agency credits (event-001, CSV).
- **The two income ranges differ slightly.** event-001 says £150–£300, but the CSV's highest credit is £285.00. The plan uses £150–£285, which is the range the itemised CSV shows.
- **The CSV doesn't list every transaction.** The running balances don't follow from the listed rows alone. For example, the balance after the £210.00 credit on 14 Aug is £1,913.15, down from £2,428.40. The £96.00 balance still matches event-001.
- **The balance is too low for either amount.** £96 is less than both £500 and £400, and there is no overdraft (event-001).
- **We can't confirm the landlord or agency agreed.** The only evidence is what the customer said (event-004). The bank has no record of it.
- **What's missing** (from the plan):
  - Whether the processing cut-off still lets the change apply to the 1 October 2026 payment. No cut-off information was supplied.
  - Confirmation from the team that the change was processed. No systems are connected, so only proposals are possible.
  - Whether the customer agrees to a financial support referral, and how they'd like to be contacted.

## 3. Why this plan
The plan cites internal skill handling rules (`skill:scheduled-payments` and `skill:vulnerability-support`). These are not supplied bank policies or legal obligations, and no specific policy clause or statute was provided.

- **s1: amend the standing order.**
  - *Why:* the customer passed ID&V, gave a clear instruction on their own account, and confirmed it again after acknowledging that £400 is less than the rent. The amount is the only thing they want changed now.
  - *Evidence:* event-001, event-002, event-003, event-004.
  - *Rule applied:* match the instruction, the next due date and the intended change, and reuse the existing schedule. Disclosed vulnerability alone doesn't justify refusing a request the bank supports.
  - *Source:* skill:scheduled-payments.
  - The £550 increase is left out because it is only a future intention.
- **s2: tell the customer (depends on s1).**
  - *Why:* the customer needs to know exactly what was changed and how far it goes. The balance is below £400 and the bank has no record of the agency's agreement, so the reply mustn't promise more than has happened.
  - *Evidence:* event-001, event-004, CSV.
  - *Rule applied:* a request to change an amount isn't a confirmed change, and amending a standing order doesn't settle a debt or contract. Report status only from the processing confirmation.
  - *Source:* skill:scheduled-payments.
- **s3: offer a referral to the financial support team.**
  - *Why:* the job loss and rent shortfall, backed by the account activity, show financial difficulty. That calls for a supportive specialist route that doesn't block the request.
  - *Evidence:* event-002, event-001, CSV.
  - *Rule applied:* for unaffordable essential living costs, refer to the right support team, respond to what the customer disclosed, and adapt the contact route.
  - *Source:* skill:vulnerability-support.
  - The referral needs the customer's consent, and only information they approve is passed on.
- **s4: point the customer to free, independent advice.**
  - *Why:* rent shortfall and uncertain income. Independent advice can help beyond what the bank can do.
  - *Evidence:* event-002, event-004.
  - *Rule applied:* refer to independent debt advice for unaffordable essential costs, and don't recommend high-cost borrowing.
  - *Source:* skill:vulnerability-support.

**Order of the steps.** s1 comes before s2 so that anything the customer is told about status is based on the team's processing confirmation. s3 and s4 don't depend on s1. They are deliberately kept separate so that support is never a condition of the change.

## 4. Where the plan stops
- s1 is a request to the standing order maintenance team, and nothing has been executed.
- Until that team confirms the change was processed, the change has to be described as pending.
- If the cut-off means the change can't apply on 1 October, the confirmation should show the first date it actually applies, and s2 should report that date.
- The referral (s3) goes ahead only if the customer agrees, and only with the information and contact method they approve.
- The plan has no escalation conditions and no other branches.

## 5. What the plan can achieve, and its limits
**Possible results:** a £400 standing order with the same payee, reference and date, starting from the first date it actually applies. Also an optional support referral and information about independent advice.

**Not guaranteed:** that the 1 October payment goes through (the balance is £96), that charges are avoided, that the agency accepts £400, or that the rent shortfall is resolved.

**What the message must say:**
- The standing order will change to £400 on the 1st from 1 October 2026, with the same payee, reference and date, and it's confirmed only once processing is confirmed.
- The £550 increase hasn't been set up, and the customer can ask for it whenever they're ready.
- The balance is £96, and a payment only goes out if there's enough money on the day.
- Help is available from the support team and from free independent advice, and using it is the customer's choice.

**What the message must not do:**
- Refuse or delay the change, or ask the customer to justify it.
- Say the change has been made before processing is confirmed.
- Say the agency or landlord has accepted £400, or that the shortfall is resolved.
- Promise the 1 October payment will go through or avoid charges.
- Set up the £550 increase.
- Recommend borrowing, or give tenancy or legal advice.
- Refer the customer without their consent, or share contact details they haven't approved.
