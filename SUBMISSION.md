# Submission

**Final repository artifacts are published.** Form delivery, registration and the organizer's
accepted freeze commit are not verified by this repository check.

- Project: dwelly-bot
- Team: Unsettled
- Track: Banking & Financial Services
- Members: Mikhail Nemilov, Vera Shishkina, Egor Pavaliev, Nikita Opletin
- Public repository: https://github.com/xmanatee/dwelly-hack-2026
- Original Opus implementation/configuration commit: `fea8324` (recorded by the actual run)
- Frozen source commit accepted by organizers: unverified; do not infer from the run receipt
- Original Opus result commit: `d8c40f9815773ee5360a589ff7f3c4cbc0fe190e`
- Final Reality Test result commit: `6346e90fa7b507e03a14a7cc615a45518d45f7ca`
- Evaluation candidate: `6346e90fa7b507e03a14a7cc615a45518d45f7ca`, with subsequent verification/documentation updates only
- Submitted evaluation commit / form receipt: unverified
- Final results: [ANSWERS/](ANSWERS/README.md), cases `001`–`030`, Banking & Financial Services
- Main demo: [demo/dashboard.mp4](demo/dashboard.mp4), 65.87 seconds
- Additional voice demo: [demo/voice-call.mp4](demo/voice-call.mp4), 46.60 seconds
- LinkedIn post: https://lnkd.in/p/efv86t2M
- X post: https://x.com/nickodp97/status/2108941052547645941
- Licence: [Apache 2.0](LICENSE)

## Results and reproducibility

The final selected set contains **21 Claude Fable 5.1 high answers and 9 Claude Opus
5.5 high answers**, with **30 complete cases and zero terminal generation errors in
the selected outputs**. Their retained journals contain 112 model requests and
approximately **$25.56** in configured-price cost estimates. This total covers the
selected outputs, not all attempts across both runs. Generation completion is not
a correctness score.

The original Opus run completed all 30 cases (98 requests, approximately $9.63).
During the organizer-extension refresh, completed Fable cases replaced their Opus
counterparts; unfinished cases retained the original Opus files byte-for-byte.
Each case retains `ANSWER.md`, `REASONING.md`, `context.md`, `plan.json` and
`generation.json`; local model journals, the report and original input hashes are included.
No answers were manually corrected. No bank actions were executed.

[Source/input manifest](ANSWERS/submission-manifest.json) ·
[Verification](ANSWERS/verification.json) · [Original run](experiments/final-challenges/README.md) ·
[Fable refresh](experiments/final-challenges-fable/README.md).

## Repository check

- Public anonymous repository and committed answer access verified.
- All 30 released banking IDs match the generated answer/reasoning folders.
- README covers product, problem, architecture, setup, models/services, assumptions,
  limitations and next steps. Locked dependencies and Apache 2.0 licence are present.
- Both committed videos decode and have video/audio streams; sample frames were inspected.
- Full offline gate after the refresh: Ruff lint and formatting passed; strict mypy
  passed for 172 source files; **361 tests passed**. No model calls were made by this check.
- All 30 answer/reasoning pairs and plans match their generation receipts; per-case
  models, configuration, costs, original/prepared input hashes and archived outputs
  were verified. The published HTML matches the selected results. Configured secrets
  were absent from tracked files and the refresh archive.
- Main demo duration is slightly above the guide's approximately 60-second target.
- Launch links are recorded; post content/authorship, individual registration and form
  receipt remain unverified. Repository readiness does not confirm form delivery.

## Timing evidence

The supplied guide says source/video freeze at **16:30 London**, results at **17:00**.
The repository records source/config/media commits around and after 16:30, and final
results at 16:39. Commit timestamps do not establish what organizers accepted or when
it was submitted. Freeze compliance needs the actual submitted commit/form receipt or
an organizer clarification; it is not claimed here. These timestamps describe the
original Opus submission. The organizer-extension refresh is recorded below; the
subsequent verification pass preserves implementation, videos and generated answers.

## Organizer-extension refresh

The user reported organizer authorization to regenerate answers until **17:10 London**.
The refresh uses implementation/config commit `789d347`; generation stopped at
**17:09 London**, and result commit `6346e90` was pushed before 17:10. The final selected
set is **21 Fable 5.1 high / 9 Opus 5.5 high**, all 30 complete. Per-case source models
and original evidence hashes are recorded in [the manifest](ANSWERS/submission-manifest.json).
The original Opus result remains in Git at `d8c40f9815773ee5360a589ff7f3c4cbc0fe190e`.
This refresh replaces only complete successful generated outputs, without manual
answer edits or a quality-score claim.
