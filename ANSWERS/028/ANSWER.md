# Case 028: INT-028, recipient credited EUR1,135 instead of the EUR1,160 estimate

## Decision
**Disposition: escalated.** We can account for the whole EUR25 difference from the records:
- **EUR10** comes from the exchange rate. The rate at execution was 1.1500. The non-binding indicative rate shown before confirmation was 1.1600.
- **EUR15** is an intermediary deduction. Only the recipient bank's advice reports it. The payment used the Shared charge option, and possible intermediary charges were disclosed before the customer confirmed.

The desk should not confirm that the recipient should have received EUR1,160. It should not promise compensation either. Because the customer is asking for compensation, the plan treats this as a complaint and sends it to the complaints team for review.

Nothing below has been done yet. Every step is proposed and pending.

## Proposed actions (in order)
1. **s1: Ask the Brackenfold Bank complaints team to register a complaint (pending).**
   - **Who and what:** Perrin Wessel (SYN-ACCT-B028), payment INT-028. The recipient, Osa Melwick, was credited EUR1,135 instead of the EUR1,160 estimate. The customer wants EUR25 compensation today and a statement that the recipient should have received the estimate.
   - **Information to pass on:**
     - The instruction at 2026-11-18 09:00: indicative rate 1.1600, estimate shown as non-binding, Shared charge option, intermediary charges disclosed.
     - The execution advice: rate 1.1500, EUR1,150 sent, GBP1,005 debited.
     - The recipient bank's advice, which came to us through the customer: EUR15 intermediary deduction, EUR1,135 credited.
     - The breakdown: EUR10 from the rate difference plus EUR15 intermediary deduction.
   - **Request:** review the compensation request and confirm registration with a reference.
2. **s2: Reply to Perrin Wessel in the authenticated chat (pending; depends on s1).** Send the message below. If the complaints team hasn't confirmed s1 yet, the reply must say registration has been requested and confirmation is pending.

## Message to the customer (draft, not sent; for when s1 is still unconfirmed)
> I've checked both advices for INT-028. The EUR25 isn't missing. Here's how it breaks down.
>
> Your EUR1,160 figure was an estimate at an indicative rate of 1.1600, and it was shown as non-binding until execution. The payment was executed at 09:08 at 1.1500 EUR per GBP, so EUR1,150 was sent for your £1,000. Your account was debited £1,005, including the separate £5 fee. That accounts for EUR10.
>
> The recipient's bank advice shows EUR1,150 arrived. It reports a EUR15 intermediary deduction, leaving EUR1,135 credited. That accounts for the remaining EUR15. You chose the Shared charge option, and possible intermediary or receiving-bank charges were disclosed before you confirmed.
>
> So I can't confirm that the recipient should have received EUR1,160.
>
> We've asked our complaints team to register your compensation request as a complaint for review. That registration hasn't been confirmed yet. I can't promise an outcome or a payment today. I'll share the complaint reference once registration is confirmed.


## Future message draft — NOT SENT

Use only after confirmed execution of: s1.

> I've checked both advices for INT-028. The EUR25 isn't missing. Here's how it breaks down. Your EUR1,160 figure was an estimate at an indicative rate of 1.1600, and it was shown as non-binding until execution. The payment was executed at 09:08 at 1.1500 EUR per GBP, so EUR1,150 was sent for your £1,000. Your account was debited £1,005, including the separate £5 fee. That accounts for EUR10. The recipient's bank advice shows EUR1,150 arrived. It reports a EUR15 intermediary deduction, leaving EUR1,135 credited. That accounts for the remaining EUR15. You chose the Shared charge option, and possible intermediary or receiving-bank charges were disclosed before you confirmed. So I can't confirm that the recipient should have received EUR1,160. I've passed your compensation request to our complaints team as a complaint for review. I can't promise an outcome or a payment today. I'll share the complaint reference once registration is confirmed.
