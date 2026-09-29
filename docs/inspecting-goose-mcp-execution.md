# Inspecting goose's MCP execution: does the action follow the evidence?

**Published:** 25 September 2026 · updated 29 September 2026
**Author:** Andrew Espira ([@espirado](https://github.com/espirado))
**AAIF projects:** [goose](https://github.com/aaif-goose/goose), [MCP](https://modelcontextprotocol.io/)
**Companion repo:** [espirado/follows-from](https://github.com/espirado/follows-from)
**Published walkthrough:** [Does the action follow the evidence?](https://espiradev.org/blog/mcp-trace-follows-from.html)

Most tooling around agents records *what* happened: which MCP tools [goose](https://github.com/aaif-goose/goose) called, and what came back. This guide asks a narrower question a goose or MCP developer can check on a real trace:

> Given the tool evidence the agent actually obtained, does its final action **follow** from that evidence?

The bundled traces are a production MCP `tools/call`: `lookup_mpfs` for CPT 99213 on [rci-knowledge](https://api.rcintell.com/v1/mcp), public CMS fee-schedule data.

The checker answers with one of three verdicts. The third one is the point.

| Verdict | Meaning |
|---|---|
| `SUPPORTED` | the evidence the action rests on is present and matches |
| `CONTRADICTED` | the evidence is present and **contradicts** the action |
| `INSUFFICIENT_EVIDENCE` | the evidence is missing, the tool failed, or the action never declared what it rests on |

Forcing a missing-evidence case into PASS or FAIL is where audits quietly lie. An honest checker says "I can't tell" out loud.

**Section 1 is the follow-along.** You do not need a live key or a goose session. You open a trace, run it, read the verdict, then change one field and run it again. Section 2 is the same loop inside goose.

## 1. Follow along: check a trace

### What you are looking at

A trace has three steps.

1. `tool_call` records the MCP call (`lookup_mpfs`, arguments `{"code": "99213"}`).
2. `tool_result` is an MCP `CallToolResult`: `isError`, and the payload in `structuredContent`. Evidence is read from `structuredContent`. A text block with the same JSON is a fallback. `isError: true` is a failed call, so there is nothing to match.
3. `action` declares **grounds**: which result it rests on, which field, and one operator (`equals`, `not_equals`, `exists`, or `in`).

The HCPCS code in this payload sits at `results[0].hcpcs_code`. Grounds name that with a dotted path, `results.0.hcpcs_code`. Integer segments index arrays. A bare `hcpcs_code` does not match: the field is on the row, and the path you named does not reach it. That verdict is `INSUFFICIENT_EVIDENCE`.

Values compare with JSON semantics: `true` is not `1`, and `20` equals `20.0`. An early version of this checker used Python's `==`, under which `1 == True`. A result of `{"covered": 1}` came back `SUPPORTED` for grounds that required `covered == true`. The JSON was well formed and the verdict was wrong for that whole class of inputs. That comparison is fixed. It is also why the grounds stay explicit. Inferring them from a transcript is where a verifier starts returning answers that parse and are systematically wrong. This follow-along does not do that inference. Same trace in, same verdict out. No model call.

This is Phase 1, exploratory. No novelty claim. The neighboring work is named in the [README](../README.md).

The lines that decide the verdict in `examples/supported.json` are:

```json
{"type": "tool_result", "call_id": "c1", "isError": false,
 "structuredContent": {"results": [{"hcpcs_code": "99213"}], "total_count": 1}}
```

```json
{"type": "action", "decision": "quote_hcpcs_99213",
 "grounds": [{"from": "c1", "field": "results.0.hcpcs_code", "equals": "99213"}]}
```

The file on disk also carries the rest of the fee-schedule row (RVUs, conversion factor, year). The checker only reads the path the grounds name.

### Install

Python 3.10 or newer. The `python3` that ships with macOS is 3.9; use a Homebrew, pyenv, or uv Python.

```bash
git clone https://github.com/espirado/follows-from.git
cd follows-from
python3 -m venv .venv && . .venv/bin/activate
pip install -e .
```

### Supported

Open `examples/supported.json`. The server returned `hcpcs_code: "99213"`. The action quotes `99213` and names `results.0.hcpcs_code`.

```bash
follows-from examples/supported.json
```

```json
{
  "verdict": "SUPPORTED",
  "decision": "quote_hcpcs_99213",
  "findings": [
    {
      "verdict": "SUPPORTED",
      "reason": "'results.0.hcpcs_code' == expected",
      "ref": "c1",
      "expected": "99213",
      "observed": "99213"
    }
  ]
}
```

Exit code `0`.

### Contradicted

`examples/contradicted.json` is the same tool result. The grounds expect `99214`.

```json
{"from": "c1", "field": "results.0.hcpcs_code", "equals": "99214"}
```

```bash
follows-from examples/contradicted.json
```

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

Exit code `1`. The observed value is what the server returned. The expected value is what the action claimed.

### Change one path

Copy the supported trace and name the top-level key instead of the row.

```bash
cp examples/supported.json /tmp/bare-field.json
```

In `/tmp/bare-field.json`, change the grounds field from `results.0.hcpcs_code` to `hcpcs_code`. Leave `equals` as `99213`.

```bash
follows-from /tmp/bare-field.json
```

```json
{
  "verdict": "INSUFFICIENT_EVIDENCE",
  "decision": "quote_hcpcs_99213",
  "findings": [
    {
      "verdict": "INSUFFICIENT_EVIDENCE",
      "reason": "field 'hcpcs_code' absent from 'c1' result",
      "ref": "c1"
    }
  ]
}
```

Exit code `2`. The code is in the payload. The path you named does not reach it, so the checker will not treat that as a match or a contradiction.

### A call that failed

`examples/insufficient.json` is the 504 we got from `tools/call` on this route. `isError` is true. There is no `structuredContent` to read. The grounds still ask for `results.0.hcpcs_code`.

```bash
follows-from examples/insufficient.json
```

```json
{
  "verdict": "INSUFFICIENT_EVIDENCE",
  "decision": "quote_hcpcs_99213",
  "findings": [
    {
      "verdict": "INSUFFICIENT_EVIDENCE",
      "reason": "tool call 'c1' failed",
      "ref": "c1"
    }
  ]
}
```

Exit code `2`. A failed call is not a contradiction: the action did not quote a code the server denied. There was no payload.

Exit codes for a verdict are `0` / `1` / `2`. If the checker cannot run (missing file, invalid JSON), it exits `3`. That is not a verdict.

## 2. Try the same loop in goose

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

## 3. The seam this leaves open

Someone still has to write the `grounds` predicate. A raw goose session does not declare what its decision rested on, so the checker returns `INSUFFICIENT_EVIDENCE`.

Turn 1 is why that line stays manual. The chat already contained the right tool name and the right code. Treating that printed JSON as a completed `tools/call`, and treating the arguments as the result, would have scored the turn `SUPPORTED`. That verdict would have parsed cleanly and been wrong: the server was never asked. This repo does not infer grounds from a transcript. The engine is deterministic and has no model calls.

## 4. A runtime boundary does not answer this

On 28 September 2026 NVIDIA announced the Open Agent Safety Platform: [OpenShell](https://developer.nvidia.com/blog/add-runtime-controls-to-ai-agents-with-nvidia-openshell/) traces agent actions and enforces policy outside the agent process, including inspected MCP traffic, and [Sentry](https://developer.nvidia.com/blog/nvidia-open-agent-safety-platform-a-reference-for-continuous-in-silicon-agent-monitoring/) can quarantine from hardware. That stack answers whether an action was allowed.

This checker answers the next question: whether the action followed from the tool result the agent obtained. Turn 1 never left the process, so an allow-list has nothing to check. `follows-from` keeps that missing evidence as its own answer.

Longer framing: [README](../README.md).

Apache-2.0.
