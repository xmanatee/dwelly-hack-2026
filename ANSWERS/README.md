# Reality Test output layout

```sh
uv run hackathon-winner /path/to/challenge/cases
```

Winner writes `ANSWERS/<original-case-folder>/ANSWER.md` and `REASONING.md` by default.
Use `--output .cache/winner/evaluation-1` for a separate evaluation run. Folder identifiers
are preserved exactly. No extra submission flag is required. Existing generated results
are never overwritten.

Each case also retains `context.md`, `plan.json` and `generation.json`. `predictions.json`
records inputs, hashes, statuses and costs; `journals/` holds actual local model traces.
There is no banking execution in this route: output actions are proposals. Failed model
cases retain their failure notices; they must not be manually replaced with corrected answers.

The bundled smoke cases and public examples are development data, regardless of output
location. Only actual challenge inputs belong in the submitted results. Generation neither
publishes this directory nor verifies eligibility. Review local journals before publication.

The older `dwelly-bot export` command remains a separate saved-execution exporter with its
own numbered-folder mapping and dataset guards. [Winner setup](../src/hackathon_winner/README.md).
