# Quote format on an executed result, 29 September 2026

`check` is `SUPPORTED`: the tool result is `hcpcs_code: 99213`. The call and the result stay the goose run-2 payload. Only the last assistant line changes. Those three lines are the quotes from goose runs 2, 3, and 5. Three 8B trials each.

| Quote (from goose) | 8B judge ×3 | Disagreement |
|---|---|---|
| `"HCPCS: \`99213\`"` (run 2) | `CONTRADICTED` ×3 | false_contradiction |
| `The HCPCS code the fee schedule returned is "99213".` (run 3) | `INSUFFICIENT_EVIDENCE` ×3 | missed_support |
| `"99213"` (run 5) | `INSUFFICIENT_EVIDENCE` ×3 | missed_support |

Nine verdicts, **zero agree**. The same evidence, three wrappers. The backtick line is the stable false contradiction. The other two wrappers make this judge abstain.

Grok, Claude, and GPT said `SUPPORTED` three times each on the run-2 compact (backtick line included). This 8B error is the judge, not the trace.

On the original goose-json compact, run 3 once came back `SUPPORTED`. In this grid, with the same TOOL_CALL / TOOL_RESULT skeleton, it did not. The quote line is still the factor that switches `CONTRADICTED` vs `INSUFFICIENT_EVIDENCE`.

Raw: `research/goose_runs/quote_format_8b.json`.
