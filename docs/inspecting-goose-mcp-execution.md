# Inspecting goose's MCP execution: does the action follow the evidence?

**Published:** 25 September 2026 · updated 29 September 2026
**Author:** Andrew Espira ([@espirado](https://github.com/espirado))
**AAIF projects:** [goose](https://github.com/aaif-goose/goose), [MCP](https://modelcontextprotocol.io/)
**Companion repo:** [espirado/follows-from](https://github.com/espirado/follows-from)

Most tooling around agents records *what* happened — which MCP tools [goose](https://github.com/aaif-goose/goose) called, and what came back. This walkthrough asks a narrower question a goose or MCP developer can run in a couple of minutes:

> Given the tool evidence the agent actually obtained, does its final action **follow** from that evidence?

The bundled traces are not a toy payer. They are the shape of a production MCP `tools/call` — `lookup_mpfs` for CPT 99213 on [rci-knowledge](https://api.rcintell.com/v1/mcp) — public CMS fee-schedule data.

The checker answers with one of three verdicts. The third one is the point.

| Verdict | Meaning |
|---|---|
| `SUPPORTED` | the evidence the action rests on is present and matches |
| `CONTRADICTED` | the evidence is present and **contradicts** the action |
| `INSUFFICIENT_EVIDENCE` | the evidence is missing, the tool failed, or the action never declared what it rests on |

Forcing a missing-evidence case into PASS or FAIL is where audits quietly lie. An honest checker says "I can't tell" out loud.

You do not need a live key or a goose session for the steps below.

## 0. What you need

- Python 3.10 or newer (the `python3` that ships with macOS is 3.9)
- About two minutes

```bash
git clone https://github.com/espirado/follows-from.git
cd follows-from
python3 -m venv .venv && . .venv/bin/activate
pip install -e .
```

## 1. Run the three verdicts

Each file under `examples/` is an MCP-shaped trace: a `tool_call`, a `tool_result` using MCP's own fields (`isError`, `structuredContent`), and a final `action` that declares its **grounds**.

```bash
follows-from examples/supported.json      # exit 0
follows-from examples/contradicted.json   # exit 1
follows-from examples/insufficient.json   # exit 2
```

The contradicted run is the one to look at. The server returned `hcpcs_code: "99213"`. The action quoted `99214`:

```json
{
  "verdict": "CONTRADICTED",
  "decision": "quote_hcpcs_99214",
  "findings": [
    {
      "verdict": "CONTRADICTED",
      "reason": "'results.0.hcpcs_code' != expected",
      "ref": "c1",
      "expected": "99214",
      "observed": "99213"
    }
  ]
}
```

The code sits under `results[0]`, not at the top level. Grounds use a dotted path: `results.0.hcpcs_code`. A bare `hcpcs_code` is `INSUFFICIENT_EVIDENCE` — the field is not absent from the world, it is absent from the path you named.

`examples/insufficient.json` is the other live miss: `tools/call` returned HTTP 504, so there is no payload to check. That is not FAIL. It is `INSUFFICIENT_EVIDENCE`.

Exit codes match the three answers (`0` / `1` / `2`). A checker that failed to run exits `3` — that is not a verdict.

## 2. Read the MCP result the way MCP sends it

A real `CallToolResult` is `isError` plus `structuredContent` (and often a text block with the same JSON). The production server now returns both. Evidence is read from `structuredContent` first.

```json
{"from": "c1", "field": "results.0.hcpcs_code", "equals": "99213"}
```

Operators: `equals`, `not_equals`, `exists`, `in`. Combine them with `all_of` / `any_of`. Values compare with JSON semantics: `true` is not `1`. Nested fields are dotted paths; integer segments index arrays.

## 3. Try the same loop in goose

Point goose at the **real** MCP server, not a mock. Config and prompts: [`goose/README.md`](../goose/README.md). You supply a live API key.

On 28 September 2026, goose with local `ollama` / `llama3.1:8b` and rci-knowledge produced two turns on the same question: look up MPFS for CPT 99213 and report the HCPCS code.

Turn 1 printed this in the chat and never called the tool. Goose showed no `▸ lookup_mpfs` line:

```text
{"name": "rci-knowledge__lookup_mpfs", "parameters": {"code": "99213"}}
```

There is no `tool_result`. The trace for that turn is `examples/unexecuted.json`. The grounds still name `c1` and `results.0.hcpcs_code`. The checker returns `INSUFFICIENT_EVIDENCE`, reason `no tool result for call 'c1'`. A well-formed tool JSON in the transcript is not evidence.

Turn 2 called `lookup_mpfs` with `code: 99213` and quoted `99213`. That is `examples/supported.json`.

| Turn | What goose did | Verdict |
|---|---|---|
| 1 | Printed tool-call JSON. No MCP call. | `INSUFFICIENT_EVIDENCE` |
| 2 | Called `lookup_mpfs`. Quoted `99213`. | `SUPPORTED` |

This is one session on an 8B local model.

```bash
follows-from examples/unexecuted.json   # exit 2
follows-from examples/supported.json    # exit 0
```

## 4. The seam this leaves open

Step 3 still has a manual line: **someone has to write the `grounds` predicate.** A raw goose session does not declare what its decision rested on, so the checker returns `INSUFFICIENT_EVIDENCE` — correctly.

Turn 1 is why that line stays manual. The chat already contained the right tool name and the right code. Treating that printed JSON as a completed `tools/call`, and treating the arguments as the result, would have scored the turn `SUPPORTED`. That verdict would have parsed cleanly and been wrong: the server was never asked. This repo does not infer grounds from a transcript. The engine is deterministic and has no model calls.

## 5. A runtime boundary does not answer this

On 28 September 2026 NVIDIA announced the Open Agent Safety Platform: [OpenShell](https://developer.nvidia.com/blog/add-runtime-controls-to-ai-agents-with-nvidia-openshell/) traces agent actions and enforces policy outside the agent process, including inspected MCP traffic, and [Sentry](https://developer.nvidia.com/blog/nvidia-open-agent-safety-platform-a-reference-for-continuous-in-silicon-agent-monitoring/) can quarantine from hardware. That stack answers whether an action was allowed.

This checker answers the next question: whether the action followed from the tool result the agent obtained. Turn 1 never left the process, so an allow-list has nothing to check. `follows-from` keeps that missing evidence as its own answer.

Longer framing: [README](../README.md).

Apache-2.0.
