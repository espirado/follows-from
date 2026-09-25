# AGENTS.md

Guidance for AI coding agents working in this repository. Humans: see `README.md`.

## What this project is

`follows-from` checks whether an agent's action follows from the tool evidence it
actually obtained, and returns one of three verdicts: `SUPPORTED`,
`CONTRADICTED`, or `INSUFFICIENT_EVIDENCE`. It is a small, honest lens on MCP
execution traces — deliberately narrow, and deliberately clear about what it does
not do.

## Build, test, run

```bash
python -m pip install -e ".[dev,demo]"
python -m pytest -q                              # must pass before commit
python -m follows_from examples/contradicted.json   # try the CLI
```

The `demo` extra (`fastmcp`) is only for `goose/` and `tests/test_goose_demo.py`,
which checks that the bundled example traces match what the mock MCP server
actually returns. If you change the mock or an example, that test must still pass.

No network, no API keys, no model calls in the core. Keep it that way.

## Conventions

- Python 3.10+, standard library only in `follows_from/check.py`. A new
  third-party import in the core will be rejected in review.
- The public API is what `follows_from/__init__.py` exports.
- Every verdict must be traceable to a `Finding` that carries the evidence
  (`ref`, `expected`, `observed`) that produced it. A verdict with no evidence
  behind it is a bug.

## The three rules that define this project (do not weaken)

1. **Keep the ternary.** Never collapse `INSUFFICIENT_EVIDENCE` into `SUPPORTED`
   or `CONTRADICTED` to make output tidier. Missing evidence is a distinct,
   first-class answer — it is the whole point of the tool.
2. **The core stays deterministic.** Same trace in, same verdict out. Any
   model-based ("infer the grounds from the transcript") lane is opt-in, lives
   outside `check.py`, and never becomes a required dependency.
3. **Do not overclaim.** This repo does not claim novelty over the agent-audit,
   trajectory-evaluation, or judge-reliability literature. Adjacent work is real
   and cited in the README. Don't add marketing that implies otherwise.

## Adding a grounds operator (the common task)

Operators live in `check.py` (`equals`, `not_equals`, `exists`, `in`). To add one:
extend `_OPS`, handle it in `_evaluate_atomic`, return a `Finding` with evidence,
and add a passing and a failing test in `tests/test_check.py`. Compare values with
`_same` (JSON equality), never bare `==`: in Python `True == 1`.

## Verification gate

Done means: tests pass and a human has read the diff. Agents may draft; a human
ships. For a tool about auditing agents, that rule is not optional.
