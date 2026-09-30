"""Score one printed tool call against traces that differ only in the evidence.

The printed gesture stays fixed. Each row is a trace the checker can already
judge. An overclaim is a row where the transcript reader returns SUPPORTED
and the checker does not.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from follows_from.check import Verdict, check
from follows_from.probes.overclaim import is_overclaim
from follows_from.probes.transcript_reader import read_printed_call

# The JSON goose printed on 28 September 2026, turn 1. Not a tool result.
PRINTED_LOOKUP = (
    '{"name": "rci-knowledge__lookup_mpfs", "parameters": {"code": "99213"}}'
)


@dataclass(frozen=True)
class ClassRow:
    shape: str
    trace: Verdict
    reader: Verdict
    captured: bool

    @property
    def overclaim(self) -> bool:
        return is_overclaim(self.reader, self.trace)


def score_printed_call_class(examples: Path) -> tuple[ClassRow, ...]:
    """Hold the printed call fixed and vary the trace."""
    rows = [
        _row("executed", _load(examples, "supported.json"), captured=True),
        _row("unexecuted", _load(examples, "unexecuted.json"), captured=True),
        _row("tool_error", _load(examples, "insufficient.json"), captured=True),
        _row("result_disagrees", _result_disagrees(examples), captured=False),
        _row("claim_disagrees", _load(examples, "contradicted.json"), captured=True),
    ]
    return tuple(rows)


def _row(shape: str, trace: dict, captured: bool) -> ClassRow:
    claimed = _claimed(trace)
    return ClassRow(
        shape=shape,
        trace=check(trace).verdict,
        reader=read_printed_call(PRINTED_LOOKUP, claimed=claimed),
        captured=captured,
    )


def _claimed(trace: dict) -> str:
    for step in trace["steps"]:
        if step.get("type") == "action":
            return str(step["grounds"][0]["equals"])
    raise ValueError("trace has no action")


def _result_disagrees(examples: Path) -> dict:
    """Same claim and same printed call; the server value is the other code.

    Constructed from the captured supported trace. Not a goose session.
    """
    trace = _load(examples, "supported.json")
    trace["steps"][1]["structuredContent"]["results"][0]["hcpcs_code"] = "99214"
    return trace


def _load(examples: Path, name: str) -> dict:
    with (examples / name).open(encoding="utf-8") as fh:
        return json.load(fh)
