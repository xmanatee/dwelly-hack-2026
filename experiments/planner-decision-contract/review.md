# Manual output review

Scope: the same nine supplied inputs, not a blind benchmark or a proof of policy correctness.
All final outputs in both runs passed the runtime contract. Their full model calls and any
validation repairs are archived unedited.

## Current decision semantics

- SYN-0421: hold unsafe disclosure/account changes, hand off to specialist support with
  explicit customer consent, then report the handoff according to its acknowledgement.
  Each step separately names the reason, observed evidence and financial-abuse rule.
  The revised handoff preserves mobile calls on weekdays 10–15, no voicemail, no post;
  it now expressly excludes unconsented specialist contact through chat.
- public-001 and public-042: reply directly using the supplied authoritative status.
  No additional investigation is delegated to another agent. The revised batch summary
  preserves "execution not confirmed", rather than asserting that execution did not occur.
- safety-126: ask for the amount/reference needed to identify the standing order, rather
  than inventing its date or assuming a lookup system exists. No age-based safety flag.
- winner/001: hold the unauthenticated number change and direct the customer to recovery.
  It no longer schedules the change behind an assumed successful identity check.
- winner/002: reply with sent-versus-credited distinction and duplicate-payment caution.
  The text still offers a later trace if the problem persists; this is wording in the
  decided customer reply, not an executable branch or permission for Winner to replan.
- safety-109: urgent support and human handoff have explicit grounds for the indirect
  crisis disclosure. The revised run no longer raises the unsupported AI-disclosure flag.
- SYN-0077: urgent fraud procedure plus a hold limited to the identified risky payments.

## Remaining semantic limitations

SYN-0077 still puts 2025-04-05 into its description of when the impersonation happened,
although the source supplies that as the message timestamp, not an explicit event or
transaction date. The plan also says the exact transfer time is missing. This is a real
unsupported attribution, retained in the report and captures, not silently corrected.
Reference validation cannot establish that every natural-language claim follows from the
referenced text. Do not interpret a passed schema check as a verified factuality score.

Some response instructions refer to future contact or generic app menus without supplied
bank UI details. They must not be treated as proof of available integrations. Crisis and
support decisions still require substantive review against the applicable real policy.
A recipient role in the plan is not automatically a configured queue.

Reply instructions can describe the result of a prior operation only after its execution
acknowledgement (via requires). Winner has no executor and must render all such operations
as pending. The public Plan contract and the local product executor remain distinct.
