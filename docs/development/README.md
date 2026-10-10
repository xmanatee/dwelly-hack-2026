# Run, configure, extend

[← Quickstart](../../README.md#quickstart) · [Repository instructions](../../AGENTS.md)

## Environment

Python **3.12**, [uv](https://docs.astral.sh/uv/), macOS/Linux or WSL. The shared budget ledger uses POSIX `fcntl` locks. Dependencies are pinned in `uv.lock`.

```sh
uv sync --locked
# Add only when working with data analysis and saved evaluation:
uv sync --locked --extra analysis --extra evaluation
```

Copy `.env.example` to `.env` only when enabling a model provider. Set the provider's key: `ANTHROPIC_API_KEY`, `OPENROUTER_API_KEY` or `OPENAI_API_KEY`. Never commit credentials. Offline demos need none of these.

## Entry points

| Command | Use |
| --- | --- |
| `dwelly-bot demo` | Current trigger/context/Planner/mock-execution path. |
| `dwelly-bot actions --profile production` | Effective action JSON schemas; also accepts `contest`. |
| `dwelly-bot agent doctor` | Inspect historical agent/provider readiness. |
| `dwelly-bot run`, `experiment` | Existing dataset agent and experiment workflow. |
| `dwelly-bot analyze` | Explicit source-data analysis recipes. |
| `dwelly-bot check` | Complete offline lint/type/test gate. |

[Demo options](../../examples/production/README.md) include `--records`, `--sqlite`, `--plan` and `--state`. Only `--context-config PATH` enables paid model-driven context investigation. That configuration uses the existing [RunConfig loader](../../src/dwelly_bot/configuration.py); choose a provider/model, request limits and a shared budget file. The default Planner remains the no-model stub.

Captures require a new output directory. `--state` points to a separate SQLite file for mock replay across processes; it is not the source database. Keep local captures and state in `.cache/`.

## Public banking data and historical experiments

```sh
uv run python dataset/fetch.py
uv run python dataset/fetch.py \
  --archive dataset/release.zip \
  --profile configs/banking-development.json \
  --root .cache/datasets/banking-reviewed
```

The first installation preserves the historical v1 snapshot. The reviewed profile corrects attachment availability without rewriting that history. Original bytes and source receipts stay ignored. [Data semantics and provenance](../../dataset/README.md).

```sh
# Offline analysis of the reviewed visible context.
uv run --extra analysis dwelly-bot analyze run dwelly_bot.analysis.banking \
  --data .cache/datasets/banking-reviewed

# Build the existing site from source analysis and saved results.
uv run --extra analysis python -m dwelly_bot.reporting.site
```

Paid experiments are separate from setup. [Experiment commands](../../experiments/README.md) and the [historical MiniMax/Sonnet protocol](../../experiments/sonnet-vs-minimax-anthropic/README.md) document the exact model/configuration receipts. They do not run the new Planner.

Account ledgers under `.cache/accounts/` retain settled costs and unresolved reservations. They are cumulative and local to a machine; an empty ledger does not establish remaining provider credit. Reuse the shared provider pool and budgeted transport rather than creating a second untracked client.

## Source map

```text
src/dwelly_bot/
├── channels/                 # input normalization and original reply routes
├── context/                  # evidence collection, sources, investigator
├── planning/                 # public contract, action profiles, stub
│   └── implementation/       # Vera's implementation slot
├── execution/                # action receipts, mock executor, durable state
├── harness/production.py     # current shared production skeleton
├── adapters/                 # existing dataset mapping and guards
├── evaluation/               # saved-result grading
└── reporting/                # reports and faithful export
examples/production/          # small runnable fixtures
experiments/                  # saved protocols, configurations and results
```

The separate `hackathon_solver` package is a target boundary, not a present directory. Keep contest-specific preparation and output generation out of the product Planner.

## Checks and contributions

```sh
uv run ruff check src tests dataset/fetch.py
uv run ruff format --check src tests dataset/fetch.py
uv run mypy
uv run pytest -q tests/test_intake_context.py tests/test_context_sources.py \
  tests/test_plan_execution.py tests/test_action_profiles.py tests/test_production_pipeline.py
```

Use `uv run dwelly-bot check` for the full offline gate. These checks do not call paid models. Follow [repo sync](../../.agents/skills/dwelly-bot-repo-sync/SKILL.md) before edits/pushes and [the experiment workflow](../../.agents/skills/dwelly-bot-experiment/SKILL.md) for model, prompt, retrieval or tool behavior changes. Preserve other contributors' changes and original run outputs.

The current implementation has no live bank connector or voice service. Context-source permissions and cross-entity joins must be defined with the actual data. [Remaining integration work](../architecture/integration-status.md).
