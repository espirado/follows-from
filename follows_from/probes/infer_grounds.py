"""Infer grounds from the tool call, then let the checker score that predicate.

The inferred premise is ``results.0.hcpcs_code`` equals the ``lookup_mpfs``
argument. The action's own claim is not read. ``check`` then runs unchanged.
"""

from __future__ import annotations

import copy
import json
from dataclasses import dataclass
from pathlib import Path

from follows_from.check import Verdict, check
from follows_from.probes.causal import (
    edit_change_result_code,
    edit_drop_tool_result,
    edit_mark_is_error,
    edit_none,
)
from follows_from.probes.overclaim import is_overclaim


@dataclass(frozen=True)
class InferRow:
    factor: str
    reference: Verdict
    inferred: Verdict
    inferred_equals: str | None
    captured: bool

    @property
    def overclaim(self) -> bool:
        return is_overclaim(self.inferred, self.reference)


def score_inferred_grounds(examples: Path) -> tuple[InferRow, ...]:
    base = _load(examples, "supported.json")
    return tuple(_row(name, edit(copy.deepcopy(base)), captured=(name == "none"))
                 for name, edit in MUTATIONS)


def with_inferred_grounds(trace: dict) -> tuple[dict, str | None]:
    """Copy ``trace`` with grounds taken from the lookup_mpfs argument.

    Returns the copy and the code that was copied. With no such call, the
    action's grounds are removed and the code is None.
    """
    out = copy.deepcopy(trace)
    code, call_id = _argument(out)
    action = _action(out)
    if code is None or call_id is None:
        action.pop("grounds", None)
        return out, None
    action["grounds"] = [{
        "from": call_id,
        "field": "results.0.hcpcs_code",
        "equals": code,
    }]
    return out, code


def edit_claim(code: str):
    def edit(trace: dict) -> dict:
        _action(trace)["grounds"][0]["equals"] = code
        return trace
    return edit


def edit_drop_tool_call(trace: dict) -> dict:
    trace["steps"] = [s for s in trace["steps"] if s.get("type") != "tool_call"]
    return trace


MUTATIONS = (
    ("none", edit_none),
    ("claim_99214", edit_claim("99214")),
    ("claim_99215", edit_claim("99215")),
    ("drop_tool_result", edit_drop_tool_result),
    ("mark_is_error", edit_mark_is_error),
    ("change_result_code", edit_change_result_code),
    ("drop_tool_call", edit_drop_tool_call),
)


def _row(factor: str, trace: dict, captured: bool) -> InferRow:
    inferred_trace, code = with_inferred_grounds(trace)
    return InferRow(
        factor=factor,
        reference=check(trace).verdict,
        inferred=check(inferred_trace).verdict,
        inferred_equals=code,
        captured=captured,
    )


def _action(trace: dict) -> dict:
    for step in trace["steps"]:
        if step.get("type") == "action":
            return step
    raise ValueError("trace has no action")


def _argument(trace: dict) -> tuple[str | None, str | None]:
    for step in trace["steps"]:
        if step.get("type") != "tool_call":
            continue
        if "lookup_mpfs" not in str(step.get("name") or ""):
            continue
        arguments = step.get("arguments")
        if not isinstance(arguments, dict) or not arguments.get("code"):
            continue
        return str(arguments["code"]), str(step.get("id") or "")
    return None, None


def _load(examples: Path, name: str) -> dict:
    with (examples / name).open(encoding="utf-8") as fh:
        return json.load(fh)
