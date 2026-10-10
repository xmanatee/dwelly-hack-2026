# Banking data-contract correction

Status: implementation and offline validation; no paid candidate execution, comparison, or baseline adoption.

The organizer supplies complete synthetic examples. Our initial projection treated a fixed two-event prefix and total attachment exclusion as the working dataset. That is a reproducible probe, but case 041 already supplies its payroll CSV at event 001. It also omits the organizer's explicit retrospective comparison step from the development workflow.

Hypothesis: explicit decision points, reviewed attachment availability, strict runtime inventories and a separate retrospective review make the local test faithful to the public format without giving the acting agent later answers. This is a data-contract claim, not a measured performance improvement.

Implementation:

- `configs/banking-development.json` records a default cutoff, optional case-specific cutoffs and nine reviewed attachment availability declarations. The default v2 snapshot exposes the early CSV in case 041 and withholds eight later attachments. Original bytes stay intact.
- The installer writes a separate pinned corpus. The adapter validates its identity, history cutoff and document inventory. Available text attachments support line citations; selecting an available unsupported PDF/image stops with an explicit error.
- Visible-only analysis and complete public-case retrospective review are separate recipes. The latter can display saved answers on the same corpus without model calls or fabricated labels.
- Public development exports cannot use the conventional `ANSWERS/` destination and carry a development-only notice elsewhere.

`config.json` preserves the baseline model, limits and cumulative account ledger. To run this new evidence condition, use `--dataset-root .cache/datasets/banking-reviewed` as documented in [the data contract](../../dataset/README.md). The regular experiment comparison command is for unchanged corpus/initial evidence and must not be used to compare v2 against v1 as if the inputs matched. A new control must be explicitly requested, recorded and reviewed before replacing the baseline reference. No execution results or spec are invented for this unrun candidate.

Offline validation covers chronological withholding, attachment availability, original-byte preservation, profile mismatch refusal, extra/future document rejection, nested citations, development identity and export boundaries. The historical execution results and baseline reference remain unchanged.

Validation receipt: `uv run dwelly-bot check` passed Ruff, formatting, strict types and **209 tests**. The reviewed default snapshot contains 50 cases / 101 visible documents; only case 041 has a visible attachment. All 50 legacy inputs still exactly match the saved baseline. Both visible-only analysis and retrospective review with saved baseline answers were generated offline; no paid model calls were made. The old baseline freshness check fails as expected because adapter execution code changed; this does not alter its saved results or constitute acceptance of a new baseline.

The subsequent user-authorized [MiniMax baseline and Sonnet experiment](../sonnet-vs-minimax-anthropic/README.md) complete the new control round on this snapshot. This proposal directory remains unrun under its original config/name; the actual captures are in the linked experiment.
