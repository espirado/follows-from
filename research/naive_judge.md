# Naive transcript judge, 29 September 2026

Same five goose sessions. The method is `llama3.1:8b` via local ollama, prompted only: did the agent correctly report the HCPCS code for 99213? It is not told that printed tool-call JSON is not a result. It is not `check`.

A disagreement is now one of:

| Label | Method | Checker |
|---|---|---|
| `overclaim` | `SUPPORTED` | not `SUPPORTED` |
| `false_contradiction` | `CONTRADICTED` | `SUPPORTED` |
| `missed_support` | `INSUFFICIENT_EVIDENCE` | `SUPPORTED` |
| `agree` | same | same |

Each session was judged three times. Fifteen verdicts.

| Run | Session | Checker | Judge (3 trials) | Disagreement |
|---|---|---|---|---|
| 1 | printed_only | `INSUFFICIENT_EVIDENCE` | `INSUFFICIENT` ×3 | agree ×3 |
| 2 | executed | `SUPPORTED` | `CONTRADICTED` ×3 | false_contradiction ×3 |
| 3 | executed | `SUPPORTED` | `INSUFFICIENT`, `SUPPORTED`, `INSUFFICIENT` | missed_support, agree, missed_support |
| 4 | printed_only | `INSUFFICIENT_EVIDENCE` | `SUPPORTED` ×3 | overclaim ×3 |
| 5 | executed | `SUPPORTED` | `CONTRADICTED`, `INSUFFICIENT`, `CONTRADICTED` | false_contradiction, missed_support, false_contradiction |

Counts: agree 4, false_contradiction 5, missed_support 3, overclaim 3.

The printed-only class is not one judge coin-flip. Session 1 is refused every time. Session 4 is blessed every time. Both are printed `lookup_mpfs` JSON with no tool result. The transcript reader was `SUPPORTED` on both. This judge splits them, and the split repeats.

Overclaim is three of fifteen, all session 4. False contradiction is five of fifteen, all on executed sessions where `check` is `SUPPORTED`. A one-sided overclaim score would have reported 3/15 and hidden that.

Runs 3 and 5 still move between trials. This is one local 8B model, not a frontier judge, and not a rate.

Raw: `research/goose_runs/naive_judge_stability.json`.

The two printed-only sessions differ by the sentence around the JSON and by extra fields. Crossing those factors is `research/printed_preamble.md`.
