# MiniMax M3 baseline

**50/50 cases executed and 50/50 retrospectively reviewed** on the corrected banking development snapshot. MiniMax M3 through OpenRouter used 161 requests and $0.11417 provider-reported charges. The common direct-Anthropic Opus 5.5 review used $2.26911 in configured-rate estimates.

Native answer-presence and retrieval checks pass on all 50; strict citation syntax passes on 44. Under the five-criterion semantic rubric, 11/50 answers pass every criterion; 33 contain judged action-status failures. All operational outcomes remain unknown. The model cannot send, log, hand over or modify anything in bank systems.

[Report](report.html) · [Raw execution](results.json.gz) · [Evaluated execution](evaluated.json.gz) · [Active reference](reference.json) · [Original execution reference](execution-reference.json) · [Full Sonnet comparison and inspection](../sonnet-vs-minimax-anthropic/README.md).

This is the active control pinned by `../baseline/reference.json`. Original v1 Sonnet files and `../baseline/historical-reference.json` remain unchanged. The incomplete OpenRouter retrospective evaluation (30 reviewed, 20 failed with HTTP 402) is preserved as `openrouter-evaluation-incomplete.json.gz` and `.html`; the final review reran all 50 through the same Anthropic configuration used for the candidate.
