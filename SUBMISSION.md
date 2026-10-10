# Submission

**Final repository artifacts are published.** Form delivery, registration and the organizer's
accepted freeze commit are not verified by this repository check.

- Project: dwelly-bot
- Team: Unsettled
- Track: Banking & Financial Services
- Members: Mikhail Nemilov, Vera Shishkina, Egor Pavaliev, Nikita Opletin
- Public repository: https://github.com/xmanatee/dwelly-hack-2026
- Run implementation/configuration commit: `fea8324` (recorded by the actual run)
- Frozen source commit accepted by organizers: unverified; do not infer from the run receipt
- Reality Test result commit: `d8c40f9815773ee5360a589ff7f3c4cbc0fe190e`
- Evaluation candidate: `d8c40f9815773ee5360a589ff7f3c4cbc0fe190e` plus subsequent documentation-only packaging
- Submitted evaluation commit / form receipt: unverified
- Final results: [ANSWERS/](ANSWERS/README.md), cases `001`–`030`, Banking & Financial Services
- Main demo: [demo/dashboard.mp4](demo/dashboard.mp4), 65.87 seconds
- Additional voice demo: [demo/voice-call.mp4](demo/voice-call.mp4), 46.60 seconds
- LinkedIn post: https://lnkd.in/p/efv86t2M
- X post: https://x.com/nickodp97/status/2108941052547645941
- Licence: [Apache 2.0](LICENSE)

## Results and reproducibility

The actual run used Claude Opus 5.5 at high effort: **30 cases, zero terminal errors,
98 requests**, approximately **$9.63** in configured-price cost estimates.
This is a generation-completion result, not a correctness score.
Each case retains `ANSWER.md`, `REASONING.md`, `context.md`, `plan.json` and
`generation.json`; local model journals, the report and original input hashes are included.
No answers were manually corrected. No bank actions were executed.

[Source/input manifest](ANSWERS/submission-manifest.json) ·
[Verification](ANSWERS/verification.json) · [Run instructions](experiments/final-challenges/README.md).

## Repository check

- Public anonymous repository and committed answer access verified.
- All 30 released banking IDs match the generated answer/reasoning folders.
- README covers product, problem, architecture, setup, models/services, assumptions,
  limitations and next steps. Locked dependencies and Apache 2.0 licence are present.
- Both committed videos decode and have video/audio streams; sample frames were inspected.
- Existing checks: 33 affected tests, Ruff and strict types passed. No new model runs
  or long tests were performed for the final packaging review.
- Main demo duration is slightly above the guide's approximately 60-second target.
- Launch links are recorded; post content/authorship, individual registration and form
  receipt remain unverified. Repository readiness does not confirm form delivery.

## Timing evidence

The supplied guide says source/video freeze at **16:30 London**, results at **17:00**.
The repository records source/config/media commits around and after 16:30, and final
results at 16:39. Commit timestamps do not establish what organizers accepted or when
it was submitted. Freeze compliance needs the actual submitted commit/form receipt or
an organizer clarification; it is not claimed here. This final pass changes documentation
and presentation only, preserving implementation, videos and generated answers.
