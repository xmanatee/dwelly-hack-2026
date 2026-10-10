# Run, configure, extend

[← Quickstart](../../README.md#quickstart) · [Repository instructions](../../AGENTS.md)

## Environment

Python **3.12**, [uv](https://docs.astral.sh/uv/), macOS/Linux or WSL. The shared budget ledger uses POSIX `fcntl` or Windows byte locks. Dependencies are pinned in `uv.lock`.

```sh
uv sync --locked
# Add only when working with data analysis and saved evaluation:
uv sync --locked --extra analysis --extra evaluation
# Full offline gate, including HTTP/voice service and synthetic adapters:
uv sync --locked --all-extras
```

The `voice` extra includes PyAudio: a full-extras installation needs PortAudio development
headers (`portaudio19-dev` on Ubuntu; `portaudio` via Homebrew on macOS). For HTTP-only
work, install `--extra server` without the microphone extra.

On a fresh checkout, copy `.env.example` to `.env` only when enabling a provider; preserve an existing `.env`. Set the provider's key: `ANTHROPIC_API_KEY`, `OPENROUTER_API_KEY` or `OPENAI_API_KEY`. Never commit credentials. Offline demos need none of these.

## Entry points

| Command | Use |
| --- | --- |
| `dwelly-bot local run` | Full product pipeline over the [synthetic bank](../../local_testing/banking/README.md); optional model collector and shared decision Planner. |
| `dwelly-bot voice ask` / `voice call` | Offline bridge check or live ElevenLabs conversation using normalized records and a fixture plan; [runbook](../../demo/LIVE-DEMO.md). |
| `dwelly-bot service` | Provision trusted sessions and serve authenticated turns; install `--extra server`. |
| `hackathon-winner` | Case folders → shared Planner → ANSWER/REASONING and traces. |
| `dwelly-bot demo` | Current trigger/context/Planner/mock-execution path. |
| `dwelly-bot actions --profile production` | Effective action JSON schemas; also accepts `contest`. |
| `dwelly-bot agent doctor` | Inspect historical agent/provider readiness. |
| `dwelly-bot run`, `experiment` | Existing dataset agent and experiment workflow. |
| `dwelly-bot analyze` | Explicit source-data analysis recipes. |
| `dwelly-bot check` | Complete offline lint/type/test gate. |

[Demo options](../../examples/production/README.md) include `--records`, `--sqlite`, `--plan` and `--state`. `--context-config PATH` enables paid context investigation; `--planner-config PATH` enables the shared decision Planner. That configuration uses the existing [RunConfig loader](../../src/dwelly_bot/configuration.py); choose a provider/model, request limits and a shared budget file. The key-free default demonstrates human-review routing.

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
├── planner/                  # canonical decision contract, skills, model implementation
├── planning/                 # legacy fixture contract, profiles, offline stub
├── service/                  # authenticated HTTP turns and durable sessions
├── execution/                # action receipts, mock executor, durable state
├── harness/production.py     # current shared production skeleton
├── adapters/                 # existing dataset mapping and guards
├── evaluation/               # saved-result grading
└── reporting/                # reports and faithful export
local_testing/banking/        # supplied generator, build recipe and ignored synthetic worlds
examples/production/          # small runnable fixtures
experiments/                  # saved protocols, configurations and results
```

The separate [`hackathon_winner` package](../../src/hackathon_winner/README.md) now implements generation/export and development predictions. It and the model-backed local pipeline share the canonical `planner.Plan`; no conversion to legacy fixture actions is needed. Keep contest-specific preparation and output generation out of the product Planner.

## Checks and contributions

```sh
uv run ruff check src tests dataset/fetch.py
uv run ruff format --check src tests dataset/fetch.py
uv run mypy
uv run pytest -q tests/test_intake_context.py tests/test_context_sources.py \
  tests/test_plan_execution.py tests/test_action_profiles.py tests/test_production_pipeline.py \
  tests/test_synthetic_bank.py
```

Use `uv run dwelly-bot check` for the full offline gate. These checks do not call paid models. Follow [repo sync](../../.agents/skills/dwelly-bot-repo-sync/SKILL.md) before edits/pushes and [the experiment workflow](../../.agents/skills/dwelly-bot-experiment/SKILL.md) for model, prompt, retrieval or tool behavior changes. Preserve other contributors' changes and original run outputs.

The current implementation has an authenticated voice/text webhook backend and a local ElevenLabs client-tool runner, but no live bank connector. The local voice demo needs `ELEVENLABS_API_KEY` and `ELEVENLABS_AGENT_ID`; it uses a prepared plan and no Anthropic call. Live device/provider availability must be checked on the presentation machine. Context-source permissions and cross-entity joins must be defined with the actual data. [Remaining integration work](../architecture/integration-status.md).
