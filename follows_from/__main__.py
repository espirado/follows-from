"""CLI: `python -m follows_from examples/contradicted.json`.

Exit codes are meant for CI use:
    0  SUPPORTED
    1  CONTRADICTED
    2  INSUFFICIENT_EVIDENCE
    3  the checker could not run (usage error, unreadable file, invalid JSON)
"""
from __future__ import annotations

import json
import sys

from .check import Verdict, check

_EXIT = {
    Verdict.SUPPORTED: 0,
    Verdict.CONTRADICTED: 1,
    Verdict.INSUFFICIENT_EVIDENCE: 2,
}
# Distinct from every verdict: a checker that failed to run has no opinion, and
# must not read as CONTRADICTED (Python's default crash code is 1) or as
# INSUFFICIENT_EVIDENCE.
_CANNOT_RUN = 3


def _error(msg: str) -> int:
    print(f"follows-from: error: {msg}", file=sys.stderr)
    return _CANNOT_RUN


def main(argv: list[str] | None = None) -> int:
    argv = sys.argv if argv is None else argv
    if len(argv) != 2:
        print("usage: python -m follows_from <trace.json>", file=sys.stderr)
        return _CANNOT_RUN
    path = argv[1]
    try:
        with open(path, encoding="utf-8") as fh:
            trace = json.load(fh)
    except OSError as e:
        return _error(f"cannot read {path}: {e.strerror or e}")
    except ValueError as e:
        return _error(f"{path} is not valid JSON: {e}")
    if not isinstance(trace, dict):
        return _error(f"{path} must contain a JSON object with a 'steps' list")
    result = check(trace)
    print(json.dumps(result.to_dict(), indent=2))
    return _EXIT[result.verdict]


if __name__ == "__main__":
    raise SystemExit(main())
