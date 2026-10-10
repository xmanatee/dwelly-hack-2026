# Reality Test outputs

- Export: `dwelly-bot export --input SAVED_RUN --output ANSWERS`, or append `--answers ANSWERS` to `dwelly-bot run`. The destination must be empty (this README may remain).
- Each case: `1/ANSWER.md`, `1/REASONING.md`, `1/trace.json`, then `2/`, etc. `manifest.json` maps numbered folders to source case IDs.
- `ANSWER.md`: actual final output, or a system review notice when execution produced none. `REASONING.md`: captured public rationale, status and action references. `trace.json`: observed inputs, tool calls/results, state and grading.
- Exception diagnostics and private model transcripts stay in local run artifacts. Exported incomplete cases require human review; this notice does not send a handover.
- Generated from the saved run, including failed/missing cases; export makes no model calls and never replaces failed answers.

The organizer public examples must not be submitted here. Keep their probe exports under ignored experiment artifacts. Only the separately released Reality Test population belongs in the final `ANSWERS/` submission. Organizer IDs must be validated against its inventory before export; the manifest records every folder mapping.

The current `dwelly-banking` adapter is development-only. Both export and the run command's output preflight reject `--output ANSWERS` / `--answers ANSWERS` for it. Other destinations receive a development review notice. No challenge adapter is implemented yet; the generic numbered export alone does not establish Reality Test eligibility or organizer-ID compatibility.
