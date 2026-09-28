"""follows-from: does an agent's action follow from the evidence it actually got?

Given an MCP execution trace, this checks the final action against the tool
evidence the agent obtained and returns one of three verdicts:

    SUPPORTED             the evidence the action rests on is present and matches
    CONTRADICTED          the evidence is present and contradicts the action
    INSUFFICIENT_EVIDENCE the evidence is missing, failed, or was never declared

The third verdict is the point. Forcing a missing-evidence case into PASS or FAIL
is where audits quietly lie; an honest checker says "I can't tell" out loud. (The
ternary follows the ActionBoundary principle: missing critical evidence should
yield INCONCLUSIVE, not a forced binary.)

Trace format: {"steps": [...]} where each step is one of

    {"type": "tool_call", "id": "c1", "name": ..., "arguments": {...}}
    {"type": "tool_result", "call_id": "c1", <an MCP CallToolResult's fields>}
    {"type": "action", "decision": ..., "grounds": <premises>}

A tool_result carries the MCP result fields as-is: `isError`, and the evidence in
`structuredContent`, or else in `content` as a single text block holding a JSON
object. (The older `ok: bool` + dict `content` shape is still accepted.)

Design notes, stated plainly because they bound what this tool can and cannot claim:
  * The core is deterministic and dependency-free. Every verdict is traceable to
    the specific evidence that produced it.
  * An action is checked against its DECLARED grounds -- an explicit predicate
    saying which tool result the action rests on. An action that declares no
    grounds is not "fine"; it is unverifiable, and returns INSUFFICIENT_EVIDENCE.
  * Values compare with JSON semantics, not Python's: `true` never equals `1`.
  * Inferring grounds from a raw transcript (what a real agent trace needs) is
    deliberately NOT done here. That inference is where a verifier can return a
    well-formed, confident, wrong answer -- and auditing that failure is the
    research thread this repo sets up, not something Phase 1 claims to solve.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

__all__ = ["Verdict", "Finding", "Result", "check"]


class Verdict(str, Enum):
    SUPPORTED = "SUPPORTED"
    CONTRADICTED = "CONTRADICTED"
    INSUFFICIENT_EVIDENCE = "INSUFFICIENT_EVIDENCE"


# ordering used to aggregate atomic findings under all_of: a contradiction on any
# premise dominates, because an action resting on a false premise is contradicted
# regardless of what else holds; missing evidence dominates a clean match.
_ALL_OF_PRECEDENCE = {
    Verdict.CONTRADICTED: 0,
    Verdict.INSUFFICIENT_EVIDENCE: 1,
    Verdict.SUPPORTED: 2,
}


@dataclass
class Finding:
    """One resolved atomic premise, with the evidence that decided it."""
    verdict: Verdict
    reason: str
    ref: str | None = None          # the tool call_id the premise pointed at
    expected: Any = None
    observed: Any = None

    def to_dict(self) -> dict[str, Any]:
        d = {"verdict": self.verdict.value, "reason": self.reason}
        if self.ref is not None:
            d["ref"] = self.ref
        if self.expected is not None or self.observed is not None:
            d["expected"] = self.expected
            d["observed"] = self.observed
        return d


@dataclass
class Result:
    verdict: Verdict
    decision: str | None
    findings: list[Finding] = field(default_factory=list)
    summary: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "verdict": self.verdict.value,
            "decision": self.decision,
            "findings": [f.to_dict() for f in self.findings],
            "summary": self.summary,
        }


# --- trace access ------------------------------------------------------------


def _steps(trace: dict[str, Any]) -> list[dict[str, Any]]:
    steps = trace.get("steps")
    if not isinstance(steps, list):
        return []
    return [s for s in steps if isinstance(s, dict)]


def _final_action(trace: dict[str, Any]) -> dict[str, Any] | None:
    actions = [s for s in _steps(trace) if s.get("type") == "action"]
    return actions[-1] if actions else None


def _result_for(trace: dict[str, Any], call_id: str) -> dict[str, Any] | None:
    for s in _steps(trace):
        if s.get("type") == "tool_result" and s.get("call_id") == call_id:
            return s
    return None


def _failed(result: dict[str, Any]) -> bool:
    return result.get("isError") is True or result.get("ok") is False


def _payload(result: dict[str, Any]) -> dict[str, Any] | None:
    """The structured fields a tool result carries, or None if it carries none."""
    structured = result.get("structuredContent")
    if isinstance(structured, dict):
        return structured
    content = result.get("content")
    if isinstance(content, dict):
        return content
    if isinstance(content, list):
        texts = [b.get("text") for b in content
                 if isinstance(b, dict) and b.get("type") == "text"]
        if len(texts) == 1 and isinstance(texts[0], str):
            try:
                parsed = json.loads(texts[0])
            except ValueError:
                return None
            if isinstance(parsed, dict):
                return parsed
    return None


def _same(a: Any, b: Any) -> bool:
    """JSON equality. Python's == says True == 1; JSON's true is not the number 1."""
    if isinstance(a, bool) or isinstance(b, bool):
        return isinstance(a, bool) and isinstance(b, bool) and a == b
    if isinstance(a, list) and isinstance(b, list):
        return len(a) == len(b) and all(_same(x, y) for x, y in zip(a, b))
    if isinstance(a, dict) and isinstance(b, dict):
        return a.keys() == b.keys() and all(_same(a[k], b[k]) for k in a)
    return a == b


def _lookup(payload: dict[str, Any], path: str) -> tuple[bool, Any, str | None]:
    """Resolve `field`, including dotted paths (`results.0.hcpcs_code`).

    A path with no dots is a top-level key. Dots walk objects; integer segments
    index arrays (0-based, no negatives). A malformed path returns a problem
    string; a well-formed path that isn't there is simply absent.
    """
    if "." not in path:
        if path in payload:
            return True, payload[path], None
        return False, None, None

    parts = path.split(".")
    if any(p == "" for p in parts):
        return False, None, f"field path '{path}' is malformed"
    node: Any = payload
    for part in parts:
        if isinstance(node, dict):
            if part not in node:
                return False, None, None
            node = node[part]
            continue
        if isinstance(node, list):
            if part.startswith("-") or not part.isdigit():
                return False, None, None
            idx = int(part)
            if idx >= len(node):
                return False, None, None
            node = node[idx]
            continue
        return False, None, None
    return True, node, None


# --- atomic premise evaluation ----------------------------------------------

_OPS = ("equals", "not_equals", "exists", "in")


def _evaluate_atomic(trace: dict[str, Any], atomic: Any) -> Finding:
    if not isinstance(atomic, dict):
        return Finding(Verdict.INSUFFICIENT_EVIDENCE,
                       f"premise is not an object: {atomic!r}")

    ref = atomic.get("from")
    field_name = atomic.get("field")

    ops = [o for o in _OPS if o in atomic]
    if len(ops) != 1:
        problem = "names no operator" if not ops else f"names {len(ops)} operators"
        return Finding(Verdict.INSUFFICIENT_EVIDENCE,
                       f"premise on '{ref}' {problem} (use exactly one of "
                       f"{', '.join(_OPS)})", ref=ref)
    op = ops[0]
    if not isinstance(field_name, str):
        return Finding(Verdict.INSUFFICIENT_EVIDENCE,
                       f"premise on '{ref}' names no field", ref=ref)
    if op == "in" and not isinstance(atomic["in"], list):
        return Finding(Verdict.INSUFFICIENT_EVIDENCE,
                       f"premise on '{ref}': 'in' needs a list of allowed values",
                       ref=ref)

    result = _result_for(trace, ref) if ref else None
    if result is None:
        return Finding(Verdict.INSUFFICIENT_EVIDENCE,
                       f"no tool result for call '{ref}'", ref=ref)
    if _failed(result):
        return Finding(Verdict.INSUFFICIENT_EVIDENCE,
                       f"tool call '{ref}' failed", ref=ref)

    content = _payload(result)
    if content is None:
        return Finding(Verdict.INSUFFICIENT_EVIDENCE,
                       f"result for '{ref}' carries no structured fields to check",
                       ref=ref)

    present, observed, path_problem = _lookup(content, field_name)
    if path_problem:
        return Finding(Verdict.INSUFFICIENT_EVIDENCE, path_problem, ref=ref)

    if op == "exists":
        want = atomic["exists"]
        if not isinstance(want, bool):
            return Finding(Verdict.INSUFFICIENT_EVIDENCE,
                           f"premise on '{ref}': 'exists' needs true or false",
                           ref=ref)
        ok = present is want
        return Finding(
            Verdict.SUPPORTED if ok else Verdict.CONTRADICTED,
            f"field '{field_name}' {'present' if present else 'absent'}, expected "
            f"{'present' if want else 'absent'}",
            ref=ref, expected=want, observed=present,
        )

    if not present:
        return Finding(Verdict.INSUFFICIENT_EVIDENCE,
                       f"field '{field_name}' absent from '{ref}' result", ref=ref)

    if op == "equals":
        ok = _same(observed, atomic["equals"])
        return Finding(Verdict.SUPPORTED if ok else Verdict.CONTRADICTED,
                       f"'{field_name}' {'==' if ok else '!='} expected",
                       ref=ref, expected=atomic["equals"], observed=observed)
    if op == "not_equals":
        ok = not _same(observed, atomic["not_equals"])
        return Finding(Verdict.SUPPORTED if ok else Verdict.CONTRADICTED,
                       f"'{field_name}' {'!=' if ok else '=='} forbidden value",
                       ref=ref, expected={"not": atomic["not_equals"]}, observed=observed)
    # op == "in"
    allowed = atomic["in"]
    ok = any(_same(observed, v) for v in allowed)
    return Finding(Verdict.SUPPORTED if ok else Verdict.CONTRADICTED,
                   f"'{field_name}' {'in' if ok else 'not in'} allowed set",
                   ref=ref, expected=allowed, observed=observed)


# --- grounds aggregation -----------------------------------------------------


def _normalize_grounds(grounds: Any) -> tuple[str, list[Any], str | None]:
    """Return (mode, atomics, problem). A bare list is all_of; a bare premise is
    a one-premise all_of. `problem` is set when there is nothing checkable."""
    if isinstance(grounds, list):
        mode, atomics = "all_of", grounds
    elif isinstance(grounds, dict) and ("all_of" in grounds) != ("any_of" in grounds):
        mode = "all_of" if "all_of" in grounds else "any_of"
        atomics = grounds[mode]
        if not isinstance(atomics, list):
            return mode, [], f"'{mode}' must be a list of premises"
    elif isinstance(grounds, dict) and "from" in grounds:
        mode, atomics = "all_of", [grounds]
    else:
        return "all_of", [], ("grounds must be a premise, a list of premises, or "
                              "one all_of/any_of block")
    if not atomics:
        return mode, [], "grounds declare no premises"
    return mode, atomics, None


def _aggregate(mode: str, findings: list[Finding]) -> Verdict:
    verdicts = [f.verdict for f in findings]
    if mode == "any_of":
        if Verdict.SUPPORTED in verdicts:
            return Verdict.SUPPORTED
        if Verdict.INSUFFICIENT_EVIDENCE in verdicts:
            return Verdict.INSUFFICIENT_EVIDENCE
        return Verdict.CONTRADICTED
    # all_of
    return min(verdicts, key=lambda v: _ALL_OF_PRECEDENCE[v])


# --- public entry point ------------------------------------------------------


def check(trace: dict[str, Any]) -> Result:
    """Check the final action in a trace against its declared grounds."""
    action = _final_action(trace)
    if action is None:
        return Result(
            Verdict.INSUFFICIENT_EVIDENCE, None,
            [Finding(Verdict.INSUFFICIENT_EVIDENCE, "trace contains no action step")],
            summary="trace declares no action to check",
        )

    decision = action.get("decision")
    grounds = action.get("grounds")
    if grounds is None:
        return Result(
            Verdict.INSUFFICIENT_EVIDENCE, decision,
            [Finding(Verdict.INSUFFICIENT_EVIDENCE,
                     "action declared no grounds, so it cannot be verified")],
            summary="ungrounded action: cannot tell whether it follows from evidence",
        )

    mode, atomics, problem = _normalize_grounds(grounds)
    if problem is not None:
        return Result(
            Verdict.INSUFFICIENT_EVIDENCE, decision,
            [Finding(Verdict.INSUFFICIENT_EVIDENCE, problem)],
            summary=f"action '{decision}' cannot be verified: {problem}",
        )

    findings = [_evaluate_atomic(trace, a) for a in atomics]
    verdict = _aggregate(mode, findings)

    reasons = "; ".join(f.reason for f in findings)
    summary = f"action '{decision}' is {verdict.value} by its evidence ({reasons})"
    return Result(verdict, decision, findings, summary)
