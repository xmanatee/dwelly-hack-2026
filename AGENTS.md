# Development

- Python + Pydantic AI; use uv. [README](README.md) owns setup and checks.
- Target architecture: [context → planner → execution](docs/architecture/README.md). One shared planner consumes prepared context and skills and returns a structured plan without business tool calls; context collection, execution and channel delivery are separate. The current runtime predates this migration.
- Before editing, and again before an authorized push, follow [dwelly-bot-repo-sync](.agents/skills/dwelly-bot-repo-sync/SKILL.md). Work on `main`; preserve concurrent changes.
- Agent behaviour, model/config, runtime prompts/skills, retrieval or tool changes: follow [dwelly-bot-experiment](.agents/skills/dwelly-bot-experiment/SKILL.md).
- Data exploration: use [analyze](.agents/skills/analyze/SKILL.md); [analysis/README.md](analysis/README.md) owns recipe usage. Analysis findings become agent changes only through the experiment workflow.
- Banking data semantics: [dataset/README.md](dataset/README.md) owns the organizer contract. Full public-case study is retrospective; runtime evidence is an explicit decision-time projection. Preserve development/challenge identity, review attachment availability, and never replay later history as live tool results.
- Report styling, docs, tests and coding instructions: relevant offline checks; no paid benchmark by default.
- After each successfully addressed request, commit this task's changes. Use quick, targeted validation; do not regenerate artifacts or run heavy checks unless needed or requested. Push only when requested.
- Format Python with Ruff; keep lint, strict types and affected tests passing.
- Keep dataset mapping/guards in adapters, agent orchestration in the harness, saved-result grading in evaluation and display in reporting. Reuse the common runner, model pool, budget and journal; analytics must not import private evaluator labels.
- Shared application: `src/dwelly_bot/`; experiment specs: `experiments/`; original corpus: ignored `dataset/`. Preserve original data bytes and actual run outputs.
- Coding skills: edit `.agents/skills/`; `.claude/skills/` links to those same files. Runtime prompts/skills belong in `src/dwelly_bot/`.
- Keep credentials in environment variables. Do not enable vendor telemetry or session capture.
