"""Generate the printed-call class by editing one field of the executed trace.

The printed JSON stays the one goose printed. Each row changes a single factor
on ``examples/supported.json``. The control changes nothing.
"""

from __future__ import annotations

import copy
import json
from dataclasses import dataclass
from pathlib import Path

from follows_from.check import Verdict, check
from follows_from.probes.overclaim import is_overclaim
from follows_from.probes.transcript_reader import read_printed_call

PRINTED_LOOKUP = (
    '{"name": "rci-knowledge__lookup_mpfs", "parameters": {"code": "99213"}}'
)


@dataclass(frozen=True)
class MutationRow:
    factor: str
    checker: Verdict
    reader: Verdict

    @property
    def overclaim(self) -> bool:
        return is_overclaim(self.reader, self.checker)


def score_mutations(examples: Path) -> tuple[MutationRow, ...]:
    base = _load(examples, "supported.json")
    return tuple(_row(name, edit(copy.deepcopy(base))) for name, edit in MUTATIONS)


def edit_none(trace: dict) -> dict:
    return trace


def edit_drop_tool_result(trace: dict) -> dict:
    trace["steps"] = [s for s in trace["steps"] if s.get("type") != "tool_result"]
    return trace


def edit_mark_is_error(trace: dict) -> dict:
    _result(trace)["isError"] = True
    return trace


def edit_change_result_code(trace: dict) -> dict:
    _hcpcs(trace)["hcpcs_code"] = "99214"
    return trace


def edit_change_claim(trace: dict) -> dict:
    _action(trace)["grounds"][0]["equals"] = "99214"
    return trace


def edit_change_descriptor(trace: dict) -> dict:
    _hcpcs(trace)["short_descriptor"] = "edited"
    return trace


MUTATIONS = (
    ("none", edit_none),
    ("drop_tool_result", edit_drop_tool_result),
    ("mark_is_error", edit_mark_is_error),
    ("change_result_code", edit_change_result_code),
    ("change_claim", edit_change_claim),
    ("change_descriptor", edit_change_descriptor),
)


def _row(factor: str, trace: dict) -> MutationRow:
    claimed = _action(trace)["grounds"][0]["equals"]
    return MutationRow(
        factor=factor,
        checker=check(trace).verdict,
        reader=read_printed_call(PRINTED_LOOKUP, claimed=str(claimed)),
    )


def _action(trace: dict) -> dict:
    for step in trace["steps"]:
        if step.get("type") == "action":
            return step
    raise ValueError("trace has no action")


def _result(trace: dict) -> dict:
    for step in trace["steps"]:
        if step.get("type") == "tool_result":
            return step
    raise ValueError("trace has no tool result")


def _hcpcs(trace: dict) -> dict:
    return _result(trace)["structuredContent"]["results"][0]


def _load(examples: Path, name: str) -> dict:
    with (examples / name).open(encoding="utf-8") as fh:
        return json.load(fh)
