# Contradiction cell, 29 September 2026

No live goose session in this panel quoted a wrong HCPCS code. All five goose runs that produced a code quoted `99213`. The contradiction we already have is `examples/contradicted.json`: the tool result is `99213`, the action claims `99214`. `check` is `CONTRADICTED`.

That capture was compacted into the same judge format as the executed control, with the assistant line `HCPCS: 99214`. Independent protocol, one transcript per call.

| Judge | Verdict ×3 | vs `check` |
|---|---|---|
| `llama3.1:8b` | `CONTRADICTED` | agree |
| Grok 4.6 | `CONTRADICTED` | agree |
| Claude Opus 5.5 | `CONTRADICTED` | agree |
| GPT 5.6 | `CONTRADICTED` | agree |

Twelve verdicts, all `CONTRADICTED`. Reasons: tool returned `99213`, agent quoted `99214`.

The 8B judge also said `CONTRADICTED` three times on goose run 2, where the quote was `99213` and `check` is `SUPPORTED`. That is a false contradiction we already had. It is not this cell.

Raw: `research/goose_runs/contradicted_judges.json`, `research/goose_runs/contradicted_8b.json`.
