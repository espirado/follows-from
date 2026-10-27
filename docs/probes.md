# Probes: score a verifier against the MCP result

**Published:** 27 October 2026
**Author:** Andrew Espira ([@espirado](https://github.com/espirado))
**Published page:** [espiradev.org/blog/follows-from-probes.html](https://espiradev.org/blog/follows-from-probes.html)
**Argument:** [When a verifier says SUPPORTED and the trace does not](https://espiradev.org/blog/verifier-overclaim.html)

A gateway decides whether a `tools/call` may run. This package does the next check: given a method that returns `SUPPORTED`, `CONTRADICTED`, or `INSUFFICIENT_EVIDENCE`, did it read the MCP result — or something else?

The reference is `follows-from` on the trace as written. A stand-in is any other method you score against that reference. An **overclaim** is the row where the stand-in said `SUPPORTED` and the reference did not.

The stand-ins live in `follows_from.probes`. They are not imported by `check()`. The public package still exports only `check`, `Verdict`, `Finding`, and `Result`. A third-party import in the core is still a reject.

This page is the apparatus. The tables and the claim are in the [post](https://espiradev.org/blog/verifier-overclaim.html).

## What you run

No API key. No model. Python 3.10 or newer.

```bash
git clone https://github.com/espirado/follows-from.git
cd follows-from
python3 -m venv .venv && . .venv/bin/activate
pip install -e ".[dev]"
python -m pytest -q \
  tests/test_overclaim.py \
  tests/test_class_score.py \
  tests/test_causal.py \
  tests/test_python_eq.py \
  tests/test_infer_grounds.py
```

`follows_from.probes.live_mcp` is not in that list. It talks to a hosted server. Do not run it unless you mean to.

## What an overclaim is

`follows_from.probes.overclaim.classify` compares two verdicts.

| Label | Method | Reference (`check`) |
|---|---|---|
| `overclaim` | `SUPPORTED` | not `SUPPORTED` |
| `false_contradiction` | `CONTRADICTED` | `SUPPORTED` |
| `missed_support` | `INSUFFICIENT_EVIDENCE` | `SUPPORTED` |
| `agree` | same | same |

The blog measures the first row. The other labels exist so a disagreement is not silently folded into “overclaim.” A method that contradicts a supported result is a different error.

## Three stand-ins

Each one trusts a different channel. That is the point of having more than one.

**Printed JSON.** `transcript_reader` returns `SUPPORTED` when a printed `lookup_mpfs` parameter equals the claim. It never reads `tool_result`. The printed string is the one goose wrote on an unexecuted turn:

```text
{"name": "rci-knowledge__lookup_mpfs", "parameters": {"code": "99213"}}
```

`class_score` holds that string fixed and scores five traces (executed, unexecuted, failed call, different result, different claim). `causal` starts from `examples/supported.json` and changes one field at a time. Same class, two ways to generate it. `goose_runs` scores the five captured `goose run` sessions in `research/goose_runs/`.

**Language equality.** `python_eq` reconstructs the old comparison: Python `1 == True`. The current checker uses JSON equality and does not import this module. The stand-in is there so the bool/int collisions stay reproducible after the fix.

**Copied arguments.** `infer_grounds` copies the `lookup_mpfs` argument into a premise and calls `check` on that premise. The action’s written claim is not an input. When the claim is a different code and the argument and the result match, the inferred verdict is `SUPPORTED`. It is right about the request. It is silent about the decision.

## What this is not

It is not a sandbox. It does not pin a tool definition, hold a credential, or allow or deny `tools/call`. OpenShell, Cordon, and the rest sit in front of the call. These probes sit after a verdict and ask what the verdict read.

It is not a rate. The five goose sessions are one model, one tool, one prompt. The causal rows are edits of one capture.

It does not detect a poisoned description or a rug-pulled server. It labels when a confident yes did not have the MCP result behind it.

## Layout

| Path | Job |
|---|---|
| `follows_from/probes/overclaim.py` | Labels a method against `check`. |
| `follows_from/probes/transcript_reader.py` | Reads printed `lookup_mpfs` JSON. |
| `follows_from/probes/class_score.py` | One printed JSON, five traces. |
| `follows_from/probes/causal.py` | One-edit mutations of the executed capture. |
| `follows_from/probes/python_eq.py` | Reconstructs `1 == True`. |
| `follows_from/probes/infer_grounds.py` | Copies the tool-call argument into a premise. |
| `follows_from/probes/goose_runs.py` | Scores captured goose sessions. |
| `research/goose_runs/` | Five `goose run` captures. |

`naive_judge` can compact a session for an optional local model. It is not required for the tests above and it is not a dependency of `check`.

Apache-2.0. Phase 1, exploratory. No novelty claim.
