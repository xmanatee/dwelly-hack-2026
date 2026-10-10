# Development

- Python + Pydantic AI; use uv. [README](README.md) owns setup and checks.
- Architecture: [context → planner → execution](docs/architecture/README.md). The public Planner is `text → Plan`; skills/configuration stay inside it. Plans contain decisions and concrete actions; execution does not repeat business reasoning. Channel replies are plan actions. The product uses the shared canonical Planner with `--planner-config`; the offline default retains a human-review fixture. Execution is mock. `hackathon_winner` imports the same Planner and separately generates answer/reasoning; the historical agent remains separate.
- Planner implementation, knowledge and skills belong to Vera in `src/dwelly_bot/planner/`; `service.DecisionPlanner` adapts text to its canonical contract. `planning/` retains legacy fixture APIs. Keep context gathering and Winner rendering separate from the Planner. See [integration status](docs/architecture/integration-status.md).
- Before editing, and again before an authorized push, follow [dwelly-bot-repo-sync](.agents/skills/dwelly-bot-repo-sync/SKILL.md). Work on `main`; preserve concurrent changes.
- Agent behaviour, model/config, runtime prompts/skills, retrieval or tool changes: follow [dwelly-bot-experiment](.agents/skills/dwelly-bot-experiment/SKILL.md).
- Data exploration: use [analyze](.agents/skills/analyze/SKILL.md); [analysis/README.md](analysis/README.md) owns recipe usage. Analysis findings become agent changes only through the experiment workflow.
- Banking data semantics: [dataset/README.md](dataset/README.md) owns the organizer contract. Full public-case study is retrospective; runtime evidence is an explicit decision-time projection. Preserve development/challenge identity, review attachment availability, and never replay later history as live tool results.
- Report styling, docs, tests and coding instructions: relevant offline checks; no paid benchmark by default.
- Plan work as small, independently reviewable stages. For each stage: sync, inspect what teammates already implemented, adjust the plan, implement only the remaining work, validate, sync again and resolve conflicts, then commit and push that stage. The user has authorized these stage-by-stage pushes; do not wait until the entire request is finished. Follow the repo-sync skill throughout and preserve unrelated work.
- Use quick, targeted validation; do not regenerate artifacts or run heavy checks unless needed or requested. After integrating concurrent changes, rerun checks affected by the combined result before pushing.
- Format Python with Ruff; keep lint, strict types and affected tests passing.
- Keep dataset mapping/guards in adapters, agent orchestration in the harness, saved-result grading in evaluation and display in reporting. Reuse the common runner, model pool, budget and journal; analytics must not import private evaluator labels.
- Shared application: `src/dwelly_bot/`; experiment specs: `experiments/`; original corpus: ignored `dataset/`. Preserve original data bytes and actual run outputs.
- Coding skills: edit `.agents/skills/`; `.claude/skills/` links to those same files. Runtime prompts/skills belong in `src/dwelly_bot/`.
- Keep credentials in environment variables. Do not enable vendor telemetry or session capture.
