# Voice research agenda

Use the relevant questions to investigate the released challenge, not as a mandatory feature list. Seek enough primary evidence to distinguish the viable options and their failure modes. Narrow the scope to the remaining build window; do not spend the day surveying providers or implementing a speculative architecture.

## Event facts and open questions

Sources to recheck at invocation:

- [Luma event page](https://luma.com/ja5x0m76).
- [Organizer rules, judging and submission guide](https://docs.google.com/document/d/1VONrEJRnT3wO35qGhrwy0h_OjJ4iH2Qt40CCuquYMXI/edit). If unavailable, use the user-supplied text and state its provenance; do not claim a live verification.
- [ElevenLabs documentation](https://elevenlabs.io/docs/overview), then the currently linked agent, speech, API, SDK, evaluation and pricing sources. Product names and capabilities must be checked again; this agenda does not pin an API contract.

From the organizer text supplied on 2026-10-10:

- Voice is an award across the four operational tracks, not a fifth track. It rewards voice inside a functioning operational workflow. The general synthetic environment may include calls, emails, documents and software records; the supplied text does not specify the representation of calls or a separate realtime voice test.
- Claude-based judging agents inspect Reality Test results, outputs, repository contents and engineering/reproducibility evidence. This does not specify whether they place calls, stream audio, run an endpoint or assess a saved demonstration. Do not fill that gap with an assumption.
- Onboarding is 09:30; development and data release begin at 10:00 London. Reality Test release is 16:30 and final results are due at 17:00. The guide conflicts about source/video freeze at 16:30 versus source freeze at 17:00. Check organizer clarification and current `SUBMISSION.md`; use 16:30 for source/video readiness until clarified. Research after the freeze cannot authorize implementation changes.

Establish from the actual release:

- Are calls audio files, transcripts, turn events, live endpoints or merely descriptions? Which languages, timestamps, speakers and stable case/customer IDs exist?
- What is an observable successful operation? Which tools and state changes are real, supplied/simulated, read-only or unavailable? Can voice ask for new facts or only process the fixed evidence?
- Is voice eligibility supported by the demo and saved workflow evidence, an organizer test, or both? What runner/input/output contract, reachable infrastructure and allowed external dependencies apply? Which details remain unknown?
- Which development cases, materials and audio may be used or published? Keep evaluator-only material and the unseen Reality Test outside research fixtures and tuning.

## Architecture choices and industry practice

Investigate public reference implementations, official SDKs and documented deployments. Explain how their constraints match this challenge; a production call centre's design may be excessive for a one-day build.

| Candidate | Questions that determine viability |
| --- | --- |
| Streaming STT → existing operational core → streaming TTS | Can turn completion, latency and cancellation fit the current core? Who coordinates partial/final input, speech and interrupts? Does the supported API provide the needed streaming behaviour? |
| Managed ElevenLabs conversational layer → backend/core | Can documented tools or a custom model integration preserve the existing reasoning, context and action checks? Who owns dialogue, tool retries, memory, final case disposition and spend? Does hosting a second decision maker introduce inconsistent authority? |
| Focused voice intake, clarification or handover → existing workflow | Does this advance a verified case outcome? Is realtime conversation needed, or is asynchronous audio sufficient? Would the reduced scope still satisfy the voice award's operational intent? |

For each viable candidate, answer the applicable questions:

- Where are retrieval and business policies applied? The authoritative backend must validate entity/case scope, arguments and state-changing tools. A transcript or voice-platform instruction is not action authority.
- Can the existing turn-based Pydantic AI runtime serve the chosen transport? Inspect actual streaming, cancellation and tool semantics instead of assuming a final-answer API is a realtime speech engine. Where would an adapter/service boundary sit without copying the harness?
- How do conversation/session IDs map to case IDs and CRM/tool state? How are disconnect/resume, parallel sessions, concurrent channel updates and context limits handled?
- What happens when a caller interrupts during a lookup or write? Distinguish stopping playback/model generation from cancelling a business operation. How are completed effects, pending actions and duplicate retries reconciled?
- How are endpointing, partial transcripts, final turns, noisy names/numbers/dates, pronunciation, language changes, silence and human handover handled? Which are necessary for this track?
- Which transports and hosting are actually supported: browser audio, WebSocket, WebRTC, telephony or server-to-server? Compare the smallest demonstrable channel; telephony is not automatically required.
- How are speech/model/platform costs and long-running sessions capped? Include minutes/characters/tokens, billing minimums, concurrency, cancellation and account balances where documented. The current LLM ledger does not automatically cover an independently running voice platform.
- Can saved evidence support reproduction when a provider dashboard or live endpoint is unavailable to judges? Keep provider inference separate from optional recordings/session capture, which must remain disabled unless specifically requested.

## Testing the realtime system

Design complementary levels; none substitutes for all the others:

1. **Core replay:** run the same development cases, source evidence and initial state as the accepted baseline. Assess outcomes, coverage, tool effects, uncertainty, escalation and failures through saved evaluation. This measures the business core, not acoustic or turn-taking quality.
2. **Dialogue/scenario tests:** exercise clarification, changing facts, missing information and handover. Research any documented provider simulations/evaluation and whether they use text or actual audio. A scripted or model-driven caller is synthetic; keep its allowed facts separate from evaluator labels and do not tailor it to flatter the agent.
3. **Audio/streaming tests:** use permitted supplied audio or explicitly labelled development fixtures, including interruption and timing. Inspect recognition errors, spoken content, turn boundaries and actual backend effects. A transcript-only replay cannot prove barge-in, microphone transport or speech latency.
4. **Working demonstration:** show a voice interaction reaching a real observed workflow outcome or a justified handover. Preserve available evidence of executed actions; saying an action happened or generating a transcript does not verify it.

Choose a small representative development suite: an ordinary successful case, an ambiguity/clarification case, a conflict/missing-evidence escalation, tool failure and interruption/duplicate-action risk where applicable. Maintain stable IDs, initial state, fixture provenance, versioned settings and honest denominators including failures. Do not manufacture official labels when none are supplied.

Select metrics that can change the architecture decision:

- **Operational:** correct/acceptable outcomes when verifiable, coverage, unsupported decisions, observed tool effects, critical violations, escalation/handover completeness and cross-case leakage.
- **Dialogue/audio:** accuracy of task-critical entities and numbers, clarification success, end-of-turn to first audible response, tool-induced delay, interruption response and recovery, disconnects and completion rate. Report timing distributions when there are enough observations; explain the measurement boundary.
- **Resources:** cost per completed case/call, audio minutes and model tokens, concurrency, deadline/resource failures and effect on ordinary text cases.

A local model judge may assess selected behaviours with a versioned rubric and source evidence; document its uncertainty and disagreements. Avoid optimizing a judge's wording instead of real outcomes. Local scores are not the organizer's official score.

## Iterative improvement and protection of the main workload

Describe a practical loop: saved failure → layer attribution → hypothesis → one bounded change → paired replay/audio checks → case-level comparison → team decision. Separate recognition/endpointing, conversational prompting, core reasoning/retrieval/tools, spoken output and orchestration failures. Change knobs independently where possible; freeze versions/settings during a comparison.

- What can be tuned cheaply with saved captures, and what genuinely needs a new paid audio/model run? Baseline answer regrading does not rerun the agent; old audio cannot validate a changed live transport.
- Which current mechanisms are reusable, and which minimal additions would be needed for audio/session fixtures, timing, external spend, journaling and reports? Route proposed additions to the correct adapters/harness/evaluation/reporting ownership; do not build a parallel voice-only experiment system.
- How does the unchanged primary workload behave with voice disabled, no voice key, a voice outage or saturated call resources? Propose an opt-in channel, isolation of state and resource limits, and graceful fallback appropriate to the case. Never silently turn a failed voice case into a successful text result.
- Compare the proposed integration with the accepted baseline on the same primary cases/corpus. Inspect per-scenario regressions, coverage, critical flags, latency and costs, not just an aggregate gain. State acceptance/rollback gates and what evidence is still missing.
- Keep development, tuning/validation and unseen Reality Test separate. Use case/customer/session-level separation when shared source context would leak between cases. Respect the actual freeze and remaining authorized budget; provider credits are not evidence of a fresh shared allowance.

End with the smallest feasible implementation plan for the recommended option, an alternative if its main assumption fails, and the specific choice the team needs to make. No prototype, provider account changes or evaluation run is necessary merely to produce that decision.
