---
name: dwelly-bot-repo-sync
description: Synchronise team changes before editing or pushing dwelly-bot; review and commit only the requested changes.
---

# Work together on main

- Inspect status, branch and upstream before editing. Preserve existing work; do not reset, clean or stash someone else's changes. With no remote/upstream, continue locally and report the missing team setup.
- With a configured team remote, fetch before editing; inspect the incoming diff for the affected components. Fast-forward a clean checkout. If local commits diverge, rebase unpublished commits, resolve conflicts and inspect the combined result. A dirty checkout needs its owners' changes preserved separately before integration; never blindly autostash.
- Before an authorized push, fetch and integrate again. If the accepted reference changed, compare the candidate against the new baseline. If combined execution code/config changed, follow `dwelly-bot-experiment`; docs/report-only changes need only affected checks. Reuse approval only for an unchanged candidate against the same baseline.
- For behaviour changes, verify `dwelly-bot experiment baseline check experiments/baseline/reference.json` after acceptance. For other edits, inspect their scope and run affected offline checks; a missing baseline does not block unrelated fixes. No automatic paid jobs or commit hooks.
- Stage only this task's source/config/tests/docs and accepted spec/reference; inspect the staged diff. Keep credentials, corpus, caches and scratch runs excluded. Include experiment configs, specs, compressed results and HTML, including unsuccessful experiments; preserve relative baseline references.
- Commit each successfully completed request after quick, targeted checks; preserve unrelated changes. Push only when requested; existing authorization needs no second confirmation. Push normally. If rejected because main moved, fetch and repeat the integration step; never force-push shared main.
