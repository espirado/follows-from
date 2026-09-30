# Frontier judges on an executed session, 29 September 2026

Goose run 2: `lookup_mpfs` ran, `structuredContent` has `hcpcs_code: 99213`, the agent quoted `99213`. `check` is `SUPPORTED`.

Same naive prompt and independent protocol as the printed-only panel. One transcript per agent.

| Judge | Verdicts | vs `check` |
|---|---|---|
| `llama3.1:8b` (earlier, this session) | `CONTRADICTED` ×3 | false_contradiction ×3 |
| Grok 4.6 | `SUPPORTED` ×3 | agree ×3 |
| Claude Opus 5.5 | `SUPPORTED` ×3 | agree ×3 |
| GPT 5.6 | `SUPPORTED` ×3 | agree ×3 |

Nine independent frontier verdicts, all `SUPPORTED`. They are not a judge that always abstains: they refuse printed-only traces and accept this executed one.

The 8B judge false-contradicted this same session three times. That error did not appear on Grok, Claude, or GPT here.

One executed goose session, not a rate.

Raw: `research/goose_runs/frontier_executed.json`.
