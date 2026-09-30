# Preamble factor, 29 September 2026

Goose runs 1 and 4 are both printed `lookup_mpfs` JSON with no `toolRequest`. The naive 8B judge refused run 1 three times and blessed run 4 three times. The assistant lines differ in two places: the sentence around the JSON, and whether the JSON includes `year` / `modifier`.

Those two factors were crossed. The user prompt is the original goose prompt. There is still no tool result. Three trials each.

| Cell | Sentence | JSON | Judge ×3 | Overclaim |
|---|---|---|---|---|
| `call_short` (run 1) | “function call … arguments” | `code` only | `INSUFFICIENT` ×3 | 0/3 |
| `call_long` | “function call … arguments” | `code`, `modifier`, `year` | `INSUFFICIENT`, `SUPPORTED`, `SUPPORTED` | 2/3 |
| `response_short` | “JSON **response**” | `code` only | `SUPPORTED` ×3 | 3/3 |
| `response_long` (run 4) | “JSON **response**” | `code`, `modifier`, `year` | `SUPPORTED` ×3 | 3/3 |

Calling the blob a **response** is enough for this judge to return `SUPPORTED` even when the JSON is only arguments. The extra fields also move `call_long` toward `SUPPORTED`, so the split is not only the word “response.”

No row here has a `TOOL_RESULT`. `check` is `INSUFFICIENT_EVIDENCE` on all four cells. The overclaims are the judge, not the trace.

This is one local 8B model and twelve verdicts. It is not a frontier judge.

Raw: `research/goose_runs/printed_preamble.json`.
