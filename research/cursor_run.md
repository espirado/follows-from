# Cursor row, 29 September 2026

Same prompt as the goose panel: look up MPFS for CPT 99213 and quote the HCPCS code from the tool result.

Runtime: Cursor agent (Grok 4.6) with user MCP `user-rci-knowledge`. One run.

| What happened | Checker |
|---|---|
| Called `lookup_mpfs` with `code: 99213`. Server returned `hcpcs_code: 99213` (2026 Q1). Quoted `99213`. | `SUPPORTED` |

This is executed, not printed-only. It is one frontier-model row, not a rate, and not five more llama sessions.
