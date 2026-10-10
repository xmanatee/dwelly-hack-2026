# Hard-case batch readiness

Requested setup: a newly supplied local Anthropic key and a strong model at high or xhigh
reasoning effort for approximately 30 hard cases. This is configuration/readiness work,
not a comparison or adoption of a new quality baseline. The saved baseline remains stale.

Configuration: [config-hard.json](../../src/hackathon_winner/config-hard.json).
The user credential is in ignored, owner-only `.env` under `ANTHROPIC_WINNER_API_KEY`;
no secret is stored in this config, evidence or Git. Existing default credentials/configs
are not overwritten. The Models API authenticated the key and lists Opus 5.5 and Fable 5.1. Official model documentation supports high effort
and a 128k output limit for Opus 5.5.

Use Opus 5.5 high (adaptive thinking), 32,768 maximum output tokens per request including
thinking, three concurrent cases, 600 seconds per request, 1,800 seconds per case,
500k total tokens per case, and two repair retries. Expanded validation ceilings retain
all existing model/run defaults. The separate cumulative ledger has a $100 local guard;
this is not a spend target, provider balance or cross-machine cap. The new 30 cases have
not arrived and have not been processed.

```sh
uv run hackathon-winner /path/to/cases --config src/hackathon_winner/config-hard.json
```

Full input size and attachment readability are checked when the actual dataset arrives.
Existing APIs retain per-case errors, evidence/authority checks, journals and output protection.

Primary sources checked on 2026-10-10:
[model overview/pricing](https://platform.claude.com/docs/en/models/overview),
[effort recommendations](https://platform.claude.com/docs/en/build-with-claude/effort).
The user clarified a $100 budget for about 30 cases. Opus 5.5 high is selected for
strong reasoning with more retry headroom: $4/input MTok and $20/output MTok, compared
with Fable 5.1 at $10/$50. The guard includes readiness calls, reservations and retries.
$100 is a ceiling, not a guarantee that any input size or number of retries will fit. A readiness smoke on bundled cases verifies the
actual transport, larger output allowance and Planner → generator path; it is not an eval
of the forthcoming hard cases.
