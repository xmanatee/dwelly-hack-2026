# ANSWER — Case 011: Refund of duplicate £1,096.00 credit (Paul Devlin t/a Devlin Plumbing)

## Decision

Proceed with the refund as a **return to source**, subject to two gates. The refund details the client supplied (sort code SYN-SC-11-2, account SYN-ACCT-11-2) are identical to the originating account of both £1,096.00 Faster Payment credits, and Confirmation of Payee on those details returned a match to "M KOWALCZYK". The "A KOWALCZYK" / "M Kowalczyk" name difference is unverified by the bank but does not block a return to the originating account. Nothing is to be sent until (1) the bank's records have been checked for an existing Meridian recall on either credit and (2) Paul confirms the payment in the secure business banking channel.

**Disposition:** needs_info (pending the recall check and Paul's secure confirmation).

## Proposed actions (in order — none executed yet)

1. **s1 — Check records (pending).** Check Harrow & Vale Bank's inbound Faster Payment / recall-and-return records for SYN-SC-11-1 / SYN-ACCT-11-1 for any recall, return request or indemnity claim from Meridian Bank relating to end-to-end IDs MER26092109401201 (21 Sep, £1,096.00) or MER26092214204811 (22 Sep, £1,096.00). Record the result on case 011 before any outbound payment is released.

2. **s2 — Set up payment for secure confirmation (pending; depends on s1).** Prepare one outbound Faster Payment of £1,096.00 from SYN-SC-11-1 / SYN-ACCT-11-1 to sort code SYN-SC-11-2, account SYN-ACCT-11-2, payee name "M Kowalczyk" (CoP matched "M KOWALCZYK" at 2026-09-23T10:05:33Z), reference "REFUND INV 2211 DUPLICATE", for Paul Devlin's confirmation in the business banking channel. Note on the case that this returns the second credit (end-to-end ID MER26092214204811) to its originating account. Release only on Paul's confirmation and only if s1 shows no existing Meridian recall for that credit.

3. **s3 — Reply to customer (pending; depends on s1 and s2).** Send the message below in the business banking chat.

## Proposed message to the customer (not yet sent)

> Thanks — that helps. The key point is that the details your client gave (SYN-SC-11-2 / SYN-ACCT-11-2) are the same sort code and account number both £1,096 payments came from, and Confirmation of Payee matches 'M KOWALCZYK' on that account. So this would be a return to the account that paid you, not a payment to a new destination. We can't verify who holds that account or confirm the relationship you've described — the payer name on the credits shows 'A KOWALCZYK' — but because it's the originating account, that doesn't block the refund. Nothing has been sent yet. I'm first checking whether the payer's bank has already asked us to return one of the payments, so you don't end up refunding twice. I'll then send you a £1,096.00 payment to those details with reference 'REFUND INV 2211 DUPLICATE' to confirm securely in your business banking; it only goes once you confirm. I can't promise an arrival time. Please keep your client's text and these payment IDs (MER26092109401201, MER26092214204811) for your records.

## What this does not do

- It does not treat the forwarded text as a verified instruction from the payer, and it does not assert that the Meridian account is joint, is Marek's, or that Anna is authorised on it.
- It does not state that no Meridian recall exists — only that none is recorded in the supplied snapshot; the s1 check is what establishes this.
- It does not request any PIN, password or one-time code in chat; confirmation happens in the secure business banking channel.
