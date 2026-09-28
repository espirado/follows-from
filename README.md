# follows-from

**Published:** 25 September 2026 · **Author:** Andrew Espira ([@espirado](https://github.com/espirado))

AAIF September tutorial (goose + MCP): [Inspecting goose's MCP execution](docs/inspecting-goose-mcp-execution.md).

**Does an agent's action follow from the evidence it actually got?**

Agent-audit tooling mostly records *what* an agent did — which tools it called,
what came back. `follows-from` asks one narrow question about that record: given
the tool evidence the agent actually obtained, does its final action **follow**
from that evidence?

It answers with one of three verdicts:

| Verdict | Meaning |
|---|---|
| `SUPPORTED` | the evidence the action rests on is present and matches |
| `CONTRADICTED` | the evidence is present and **contradicts** the action |
| `INSUFFICIENT_EVIDENCE` | the evidence is missing, the tool failed, or the action never declared what it rests on |

That third verdict is the point. Forcing a missing-evidence case into a PASS or a
FAIL is where audits quietly lie. An honest checker says "I can't tell" out loud.
(The ternary follows the principle set out by trace-backed authorization work like
[ActionBoundary](https://github.com/hugoii/llm-agent-audit): when critical
evidence is missing, the answer should be *inconclusive*, not a forced binary.)

## Quickstart

Requires Python 3.10+. (The `python3` that ships with macOS is 3.9; use a
Homebrew, pyenv, or uv Python.)

```bash
python3 -m venv .venv && . .venv/bin/activate
pip install -e .
follows-from examples/contradicted.json     # or: python -m follows_from ...
```

```json
{
  "verdict": "CONTRADICTED",
  "decision": "approve_claim",
  "findings": [
    {"verdict": "CONTRADICTED", "reason": "'covered' != expected",
     "ref": "c1", "expected": true, "observed": false}
  ],
  "summary": "action 'approve_claim' is CONTRADICTED by its evidence ('covered' != expected)"
}
```

The three bundled traces show the three verdicts: `supported.json`,
`contradicted.json`, `insufficient.json`. The engine is dependency-free and
deterministic — same trace in, same verdict out, no model calls, no keys.

Exit codes are built for CI:

| Code | Meaning |
|---|---|
| `0` | `SUPPORTED` |
| `1` | `CONTRADICTED` |
| `2` | `INSUFFICIENT_EVIDENCE` |
| `3` | the checker could not run (usage error, unreadable file, invalid JSON) |

A checker that failed to run has no opinion, so it never exits with a verdict's code.

## How it decides

A trace is a list of steps. Tool results carry the fields of an MCP
`CallToolResult` as-is (`isError`, `structuredContent`, `content`), and the final
action declares its **grounds**: an explicit predicate naming which tool result it
rests on.

```json
{"steps": [
  {"type": "tool_call", "id": "c1", "name": "get_payer_policy",
   "arguments": {"claim_id": "CLM-1002", "procedure": "X123"}},
  {"type": "tool_result", "call_id": "c1", "isError": false,
   "structuredContent": {"covered": false}},
  {"type": "action", "decision": "approve_claim",
   "grounds": [{"from": "c1", "field": "covered", "equals": true}]}
]}
```

The checker resolves each premise against the referenced result and reports the
evidence behind every finding. Evidence is read from `structuredContent`, or else
from a `content` list holding a single text block with a JSON object; a result with
`isError: true` is a failed call.

- Operators: `equals`, `not_equals`, `exists`, `in` (exactly one per premise),
  combined with `all_of` / `any_of`. A bare list means `all_of`.
- `field` may be a top-level key or a dotted path (`results.0.hcpcs_code`). Integer
  segments index arrays. A missing path is `INSUFFICIENT_EVIDENCE`, not a match.
- Values compare with JSON semantics: `true` does not equal `1`, but `20` equals `20.0`.
- A premise whose evidence is missing, whose tool call failed, or that is itself
  malformed is `INSUFFICIENT_EVIDENCE`; a premise the evidence contradicts is
  `CONTRADICTED`.
- Under `all_of`, a contradiction on any premise dominates, because an action
  resting on a false premise is contradicted whatever else holds.

Every verdict, including every `INSUFFICIENT_EVIDENCE`, comes with at least one
finding saying why.

## Try it in goose

`goose/` has a reproducible end-to-end demo: a tiny mock MCP server, the exact
goose extension config, and steps to drive goose into each of the three verdicts.
See [`goose/README.md`](goose/README.md).

## Where this sits (and what it does *not* claim)

This is a small, deliberately narrow tool, and the surrounding work is active and
more capable. In particular:

- [Microsoft AgentRx](https://github.com/microsoft/AgentRx) synthesizes invariants
  from tool schemas and policies, checks trajectories step by step with
  evidence-backed violations, and its failure taxonomy already includes
  "misinterpretation of tool output" and an "inconclusive" category.
- Provably's [SourceryKit experiment](https://provably.ai/blogs/The-Agent-Was-Right-The-Evidence-Wasnt)
  compares an agent's final claims against captured live MCP executions and
  counts the claims the trace does not support — the closest thing we know of to
  this relation, at larger scale.
- [ActionBoundary](https://github.com/hugoii/llm-agent-audit) scores whether a
  real action has runtime evidence for identity, authorization, and outcome, and
  fails closed to `INCONCLUSIVE`.
- [HazardAuditor](https://arxiv.org/abs/2609.15134) does execution-grounded safety
  auditing across agent frameworks; [ATBench](https://arxiv.org/abs/2604.02022)
  benchmarks trajectory-level safety evaluators.
- [Signet](https://github.com/Prismer-AI/signet) and various MCP audit proxies
  produce verifiable, tamper-evident records of what was called.

`follows-from` claims none of their ground. It isolates one relation —
*evidence → action consistency*, reported as an honest ternary — and makes it
runnable and inspectable in a few lines. **Status: Phase 1, exploratory. No
novelty claim.**

## Open question (where this is going)

`follows-from` is itself a verifier. And here is the uncomfortable part:

**A verifier can return a well-formed, confident, wrong answer.**

This one already has: an early version compared values with Python's `==`, under
which `1 == True`. A tool result of `{"covered": 1}` came back `SUPPORTED` for an
action resting on `covered == true` — clean JSON, a confident verdict, the wrong
answer, for a whole class of inputs. That is fixed, and it is the easy kind: the
checker's reasoning is small because it requires an *explicit* `grounds` predicate.

A real agent trace doesn't declare its grounds. To check an un-annotated goose run,
something has to *infer* what the action rested on — and that inference is exactly
where a verifier starts producing verdicts that parse cleanly, look confident, and
are systematically wrong for particular shapes of input.

So the question this repo is really pointed at is not "was the agent right?" It's:

> **Who audits the auditor — and how would you *measure* the classes of input on
> which a verifier is confidently, repeatably wrong?**

That is the thread we pick up next: a reproducible, causal way to expose a
verification method's systematic mislabel classes, rather than trusting its
verdicts because they come back well-formed. If that question is interesting to
you, the [issue tracker] is the place to poke at it.

[issue tracker]: https://github.com/OpenSecureAIAlliance/RFCs/issues

## Development

```bash
pip install -e ".[dev,demo]"
python -m pytest -q
```

The `demo` extra installs `fastmcp` so `tests/test_goose_demo.py` can drive the
mock MCP server and confirm the bundled traces match what it really returns;
without it, those tests are skipped.

CI (`.github/workflows/ci.yml`) runs the suite on Python 3.10–3.14 and checks that
the checker installs and runs with no third-party packages. To run it locally with
[act](https://github.com/nektos/act) and Docker (flags live in `.actrc`):

```bash
act                     # all jobs
act -j test             # just the test matrix
```

With colima, first point act at its socket:
`export DOCKER_HOST="$(docker context inspect --format '{{.Endpoints.docker.Host}}')"`.

## License

Apache-2.0. See `LICENSE` and `NOTICE`.
