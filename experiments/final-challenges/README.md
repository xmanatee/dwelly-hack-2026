# Final banking challenges

Run all 30 released cases from [HackatonChallenges](https://github.com/DwellyOrg/HackatonChallenges).
This is submission generation, not a development benchmark or a quality comparison.

The preparation script preserves original bytes, maps each challenge index to `request.md`,
and adds local Tesseract text transcriptions for images. All history and attachments are
supplied to the shared Planner. Original hashes are recorded in the input manifest.

The run uses Opus 5.5 high with ten concurrent cases and the existing cumulative $100 ledger.
Actual answers, reasoning, plans, inputs and model journals are retained in `ANSWERS/`.
No bank actions are executed. Failed outputs must be preserved, never hand-corrected.

```sh
uv run python experiments/final-challenges/prepare.py \
  '.cache/datasets/final-challenges/Banking & Financial Services' \
  .cache/datasets/final-banking-input/cases
uv run hackathon-winner .cache/datasets/final-banking-input/cases \
  --config experiments/final-challenges/config.json
```
