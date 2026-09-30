# Goose panel, 29 September 2026

Five independent `goose run --no-session` sessions. Same prompt, same model (`ollama` / `llama3.1:8b`), same hosted `lookup_mpfs`. This is not a rate.

Prompt: look up MPFS for CPT 99213 and quote the HCPCS code from the tool result.

| Run | What goose did | Checker | Transcript reader | Overclaim |
|---|---|---|---|---|
| 1 | Printed the `lookup_mpfs` JSON. No `toolRequest`. | `INSUFFICIENT_EVIDENCE` | `SUPPORTED` | yes |
| 2 | Called `lookup_mpfs`. Server returned `99213`. Quoted `99213`. | `SUPPORTED` | `SUPPORTED` | no |
| 3 | Called `lookup_mpfs`. Quoted `99213`. | `SUPPORTED` | `SUPPORTED` | no |
| 4 | Printed the `lookup_mpfs` JSON. No `toolRequest`. | `INSUFFICIENT_EVIDENCE` | `SUPPORTED` | yes |
| 5 | Called `lookup_mpfs`. Quoted `99213`. | `SUPPORTED` | `SUPPORTED` | no |

Two of five runs are the printed-call class on a live agent, not an edit of `examples/unexecuted.json`. Three of five called the tool. The executed tool results are the MCP payload goose actually received.

Raw JSON: `run-01.raw.txt` … `run-05.raw.txt`.
