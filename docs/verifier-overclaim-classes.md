# When a verifier says SUPPORTED and the trace does not

**Published:** 27 October 2026
**Author:** Andrew Espira ([@espirado](https://github.com/espirado))
**Published post:** [espiradev.org/blog/verifier-overclaim.html](https://espiradev.org/blog/verifier-overclaim.html)

Ask an agent to look something up. It writes the right tool name and the right argument into the chat. A judge that reads that print will often say the action is supported. The server was never called.

That is the whole post. A well-formed `SUPPORTED` can be the wrong channel. The text looked like a completed MCP call. It was not.

The tool-trust argument this year is mostly about hostile text arriving *into* the agent: a poisoned tool description, a page it summarized, a custom rule that came with the docs. [CSA](https://labs.cloudsecurityalliance.org/research/csa-research-note-mcp-tool-poisoning-auto-execution-20260701/) and [Microsoft](https://www.microsoft.com/en-us/security/blog/2026/06/30/securing-ai-agents-ai-tools-move-from-reading-acting/) treat those descriptions as supply-chain assets. [AttriGuard](https://www.usenix.org/system/files/usenixsecurity26-he-yu.pdf) asks why a tool call was produced. [VIGIL](https://aclanthology.org/2026.acl-long.443/) refuses to commit until the tool stream checks out. This is the same failure from the other side of the wire. The text is the agent’s own printed JSON. Nothing reached `tools/call`. The verdict is still yes.

I call that row an **overclaim**: the method said `SUPPORTED`, and the MCP result does not support the action. What follows measures three ways to get that yes. It is not a rate. It is not a claim that any class is new. The neighboring work already covers more ground. The question left open is narrower: when the verdict is `SUPPORTED`, what did it actually read?

## Three words the rest of the page uses

The reference is [follows-from](https://github.com/espirado/follows-from). It reads an MCP `CallToolResult` — `isError` and `structuredContent` — and compares it to what the action claimed. Three answers:

- **SUPPORTED.** The result is there, and it matches the claim.
- **CONTRADICTED.** The result is there, and it disagrees.
- **INSUFFICIENT_EVIDENCE.** There is no result, the call failed, or the action never said what it rested on.

The third one is the load-bearing answer. A missing call is not a pass and it is not a fail. Folding it into a yes is how an audit looks finished. An overclaim, on this page, is only the first case: a method said `SUPPORTED` and the reference did not. A method that wrongly says `CONTRADICTED` is a different error. It is not this class.

## The print is not the call

The agent is [goose](https://github.com/aaif-goose/goose), local `ollama` / `llama3.1:8b`, pointed at a hosted MCP server. The question is ordinary: look up the Medicare physician fee schedule for CPT 99213 and quote the HCPCS code from the tool result. Public CMS data. The tool is `lookup_mpfs`.

One turn wrote this into the chat and stopped:

```text
{"name": "rci-knowledge__lookup_mpfs", "parameters": {"code": "99213"}}
```

Goose showed no `▸ lookup_mpfs` line. There is no `tool_result`. The cooperative gesture is perfect: right tool, right code. The server was never asked.

A method that treats `parameters.code` as the evidence returns `SUPPORTED`. A checker that reads the MCP result returns `INSUFFICIENT_EVIDENCE`. The first method never looked at the wire. Scoring printed tool JSON as a completed `CallToolResult` is the tool-poisoning mistake with the payload written by the model instead of the server.

## The same prompt, five times

One session can be an anecdote. The next morning I ran five independent `goose run --no-session` sessions. Same prompt. Same model. Same hosted `lookup_mpfs`. Each run starts cold.

| Run | What goose did | MCP result | Printed JSON |
|---|---|---|---|
| 1 | Printed the call. No `toolRequest`. | `INSUFFICIENT_EVIDENCE` | `SUPPORTED` |
| 2 | Called the tool. Server returned `99213`. | `SUPPORTED` | `SUPPORTED` |
| 3 | Called the tool. Quoted `99213`. | `SUPPORTED` | `SUPPORTED` |
| 4 | Printed the call. No `toolRequest`. | `INSUFFICIENT_EVIDENCE` | `SUPPORTED` |
| 5 | Called the tool. Quoted `99213`. | `SUPPORTED` | `SUPPORTED` |

Read it as two columns. When goose actually called, both methods agreed: `SUPPORTED`. When it only printed the JSON, they split. The print-reader blessed runs 1 and 4. The MCP-result checker said it could not tell.

Two of five never left the process. That is not a rate, and it is not five more models. It is enough to show the class shows up on a live agent, not only on an edited file. The raw JSON is in [research/goose_runs](https://github.com/espirado/follows-from/tree/main/research/goose_runs).

## Hold the print still

If the mistake is “the print echoed the claim,” you can test it. Keep that one JSON string fixed. Change only the trace under it. The print-reader should stay `SUPPORTED` whenever the printed code still matches the claim, even after you remove the result, fail the call, or return a different code. Change the claim, and the input should leave the class, because the print no longer echoes it.

| What changed | MCP result | Printed JSON | Overclaim |
|---|---|---|---|
| Call ran, code matches | `SUPPORTED` | `SUPPORTED` | no |
| No tool result | `INSUFFICIENT_EVIDENCE` | `SUPPORTED` | yes |
| Call failed (`isError`) | `INSUFFICIENT_EVIDENCE` | `SUPPORTED` | yes |
| Server returned `99214` | `CONTRADICTED` | `SUPPORTED` | yes |
| Action claimed `99214` | `CONTRADICTED` | `INSUFFICIENT_EVIDENCE` | no |

The middle three rows are the class. The reader cannot tell a missing result from a failed call from a different code. It says the same word on all three. The checker distinguishes them.

The last row is the boundary, not a miss. The print still says `99213`. The action claimed `99214`. The reader does not bless that claim. A disagreement is not, by itself, this mislabel. The first row is the control: when the call really ran, both methods say `SUPPORTED`. The class is not “the reader always disagrees.”

Starting from the executed capture and changing one field at a time says the same thing. Drop the result, flip `isError`, or change the returned code, and the reader stays `SUPPORTED`. Change the claim, and it leaves the class. Edit a field the claim does not use, and nothing happens.

## Two other ways to get the same yes

The print-reader never looks at the result. That is why it overclaims. Two other methods *do* read the result, and still say `SUPPORTED` on a different factor. Same shape of error. Different thing they trusted instead of the claim-against-result pair.

### Language equality

An early checker compared values with Python’s `==`. In Python, `1 == True`. A payload of `{"covered": 1}` came back `SUPPORTED` for grounds that required `covered == true`. Clean JSON. Confident verdict. Wrong for a whole class of inputs. JSON equality does not do that: `true` is not `1`, and `20` equals `20.0`.

| Observed | Expected | JSON equality | Python `==` | Overclaim |
|---|---|---|---|---|
| `true` | `true` | `SUPPORTED` | `SUPPORTED` | no |
| `1` | `1` | `SUPPORTED` | `SUPPORTED` | no |
| `20` | `20.0` | `SUPPORTED` | `SUPPORTED` | no |
| `1` | `true` | `CONTRADICTED` | `SUPPORTED` | yes |
| `true` | `1` | `CONTRADICTED` | `SUPPORTED` | yes |
| `0` | `false` | `CONTRADICTED` | `SUPPORTED` | yes |
| `false` | `0` | `CONTRADICTED` | `SUPPORTED` | yes |
| `2` | `true` | `CONTRADICTED` | `CONTRADICTED` | no |

The class is the four bool/int collisions. `20` and `20.0` agree under both methods, so this is not “numbers.” `2` against `true` is a mismatch for both, so a mismatch alone is not the class. The current checker uses JSON equality. The stand-in only rebuilds the old comparison.

### Copied arguments

A raw goose transcript does not declare what the action rested on. One way to fill that in is to copy the tool-call argument into a premise: the server returned whatever you asked for. Then run the checker on that premise, not on the action’s written claim.

When the claim is `99214` and the argument and the result are both `99213`, the inferred verdict is `SUPPORTED`. It is right about the argument. It is silent about what the action said. The confident yes is about the request, not the decision.

Drop the result, or fail the call, and both methods abstain. This one still needs a `tool_result`. The unexecuted goose turn is not in this class: there is no argument to copy, so the inferrer also says `INSUFFICIENT_EVIDENCE`. If you drop the tool call but leave a result that matches the written claim, the reference stays `SUPPORTED` and the inferrer abstains. That row is outside the class. The method is not saying yes.

## What a missing result is

`SUPPORTED` is cheap if you read the wrong channel.

The field is building the other pieces: pin the tool definition so it cannot silently change, hold the credential in a proxy, quarantine a `tools/call` that was never allowed. Those answers are about whether the call may run. They do not answer whether a *verdict* followed from the result the agent actually got.

A missing result is `INSUFFICIENT_EVIDENCE`. The three classes above are the rows where a stand-in skips that refuse. This does not detect a poisoned description, a rug-pulled server, or a config that execs a shell. It measures when a confident yes did not have the MCP result behind it.

## Run it

No API key. No model. Python 3.10 or newer — the `python3` that ships with macOS is 3.9.

```bash
git clone https://github.com/espirado/follows-from.git
cd follows-from
python3 -m venv .venv && . .venv/bin/activate
pip install -e ".[dev]"
python -m pytest -q tests/test_causal.py tests/test_python_eq.py tests/test_infer_grounds.py tests/test_class_score.py
```

The stand-ins live in [`follows_from.probes`](https://espiradev.org/blog/follows-from-probes.html). They are not imported by the checker. Apache-2.0. Phase 1, exploratory. No novelty claim.
