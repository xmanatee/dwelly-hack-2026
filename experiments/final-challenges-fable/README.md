# Final challenge Fable refresh

User-authorized submission generation during the organizer extension to 2026-10-10 17:10 Europe/London. Reuse all 30 prepared challenge inputs and the shared Planner/Winner implementation. Run Claude Fable 5.1 at high effort, 15 cases concurrently, under the existing cumulative $100 Winner ledger.

Preserve the original Opus submission in Git and a local snapshot. Generate into a separate directory; replace only complete successful cases. Retain Opus for unfinished or failed cases. This is submission generation, not a judged quality comparison; no improvement claim or manual answer correction.

## Packaged outcome

**21 Fable 5.1 high / 9 Opus 5.5 high**, 30 complete final cases. [Case selection and refresh failures](result-summary.json), [actual run receipt](run-receipt.json), [all actual refresh files including incomplete journals](actual-refresh-results.tar.gz), [selected answer report](../../ANSWERS/report.html). The historical development baseline is stale; it was not used to claim an improvement. Original Opus outputs remain in commit `d8c40f9815773ee5360a589ff7f3c4cbc0fe190e`.

Final result commit: `6346e90fa7b507e03a14a7cc615a45518d45f7ca`. The external
`asyncio.wait_for` wrapper stopped the run at 17:09 London, retaining completed case
folders and cancelling unfinished calls. The absolute cutoff is recorded in
`run-receipt.json`; it was enforced by that wrapper, not the Winner CLI's configuration.

The refresh recorded 102 settled requests (approximately $27.26 at configured prices)
and 9 interrupted requests with uncertain usage. The ledger retains approximately
$19.86 as their conservative reserved exposure; that amount is not confirmed billing
and has not been released. The archive retains all 30 case journals, including the
interrupted attempts. The original Opus answers remain selected for cases 018, 020
and 024–030.

Post-run verification: `uv run --no-sync dwelly-bot check` passed Ruff lint/format,
strict mypy (172 source files), and all 361 offline tests. All selected answers,
reasoning and plans match their generation receipts; original/prepared input hashes,
per-case configuration and cost receipts, retained Opus bytes, archived Fable bytes
and the final HTML report were checked. No new generation or paid judging was run.
