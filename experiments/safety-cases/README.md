# Banking safety cases

28 synthetic cases in the Dwelly public-case layout (`NNN/index.md`, `history.md`, `attachments/`) for safety topics the 50 public banking cases barely cover. Fictional bank, people and organisations.

```sh
uv run python experiments/safety-cases/generate.py
```

- `generate.py` is the source; the case folders are regenerated from it. Edit cases there.
- `labels.json` is for judges only: topic, FG21/1 vulnerability driver, `decision_event` (the agent sees earlier events only), safe behaviours and unsafe behaviours. It sits outside the track folder so agents and discovery never read it.
- Topics: identity/authority, scams in progress, account takeover, financial abuse, crisis and health adjustments, financial difficulty, bereavement, complaints and rights, access to a human, accuracy and no advice, privacy, prompt injection, AI disclosure. Three controls (`control: true`) need no intervention and catch over-flagging.
- Each history shows one safe handling path; other safe paths can be valid. Synthetic expectations are not legal advice; verify against current FCA, PSR and bank policy before relying on them.
