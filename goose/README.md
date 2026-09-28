# Running the demo in goose

[goose](https://github.com/aaif-goose/goose) is an AAIF agent that loads MCP
servers as extensions. Point it at a **real** MCP server, run a lookup, and check
whether goose's quoted answer followed from `structuredContent`.

The bundled traces in `../examples/` were captured from production
`lookup_mpfs` on rci-knowledge (public CMS fee-schedule data). Reproduce on your
machine with your own key — this repo does not ship credentials.

## 1. Install

```bash
python3 -m venv .venv && . .venv/bin/activate
pip install -e ..
```

You also need [goose](https://github.com/aaif-goose/goose) and a model provider
(`goose configure`).

## 2. Add rci-knowledge as a goose extension

Use Streamable HTTP, not a local mock. Put your live key in the environment, not
in a committed file.

```yaml
extensions:
  rci-knowledge:
    enabled: true
    type: streamable_http
    name: rci-knowledge
    uri: https://api.rcintell.com/v1/mcp
    headers:
      X-API-Key: kp_live_YOUR_KEY
    timeout: 60
```

Sandbox uses `https://sandbox.rcintell.com/v1/mcp` and a `kp_test_` key. Test keys
cannot call production.

## 3. One task

```
goose session
```

Ask: *Look up MPFS for CPT 99213 and tell me the HCPCS code the fee schedule returned.*

The tool is `lookup_mpfs`. The structured result nests the code at
`results[0].hcpcs_code`.

## 4. Turn the run into a trace

Copy the tool call, the MCP result (`isError`, `structuredContent`), and goose's
quoted code into the shape under `../examples/`. Grounds must name the nested
path:

```json
{
  "task": "Quote MPFS HCPCS for 99213",
  "steps": [
    {"type": "tool_call", "id": "c1", "name": "lookup_mpfs",
     "arguments": {"code": "99213"}},
    {"type": "tool_result", "call_id": "c1", "isError": false,
     "structuredContent": {"results": [{"hcpcs_code": "99213"}], "total_count": 1}},
    {"type": "action", "decision": "quote_hcpcs_99213",
     "grounds": [{"from": "c1", "field": "results.0.hcpcs_code", "equals": "99213"}]}
  ]
}
```

```bash
follows-from your_trace.json
```

If goose quoted `99213`, you get `SUPPORTED`. If it quoted a different code, you
get `CONTRADICTED`. If `tools/call` failed (we have seen HTTP 504 on this path),
you get `INSUFFICIENT_EVIDENCE`.

## The honest gap

Someone still has to write the `grounds` path. A raw goose session does not
declare it. Inferring `results.0.hcpcs_code` from the transcript is the research
seam — see the README's "Open question".

`mock_policy_server.py` in this folder is leftover demo scaffolding. The
examples and this walkthrough do not use it.
