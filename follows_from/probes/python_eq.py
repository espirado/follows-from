"""The checker's old comparison, reconstructed outside ``check``.

Python's ``==`` treats ``1 == True`` and ``0 == False``. JSON does not. This
stand-in is the method that used to live in the checker. It is not ``check``.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from follows_from.check import Verdict, check
from follows_from.probes.overclaim import is_overclaim


@dataclass(frozen=True)
class EqRow:
    observed: Any
    expected: Any
    checker: Verdict
    python_eq: Verdict

    @property
    def overclaim(self) -> bool:
        return is_overclaim(self.python_eq, self.checker)


# Control pairs sit next to the bool/int collisions. 20 and 20.0 match under
# both methods; the class is the bool collision, not every numeric comparison.
PAIRS = (
    (True, True),
    (1, 1),
    (20, 20.0),
    (1, True),
    (True, 1),
    (0, False),
    (False, 0),
    (2, True),
)


def score_python_eq() -> tuple[EqRow, ...]:
    return tuple(_row(observed, expected) for observed, expected in PAIRS)


def python_eq_verdict(observed: Any, expected: Any) -> Verdict:
    if observed == expected:
        return Verdict.SUPPORTED
    return Verdict.CONTRADICTED


def _row(observed: Any, expected: Any) -> EqRow:
    return EqRow(
        observed=observed,
        expected=expected,
        checker=check(_trace(observed, expected)).verdict,
        python_eq=python_eq_verdict(observed, expected),
    )


def _trace(observed: Any, expected: Any) -> dict:
    return {
        "steps": [
            {
                "type": "tool_result",
                "call_id": "c1",
                "isError": False,
                "structuredContent": {"covered": observed},
            },
            {
                "type": "action",
                "decision": "approve_claim",
                "grounds": [{"from": "c1", "field": "covered", "equals": expected}],
            },
        ]
    }
