"""How a method's verdict sits relative to the checker.

An overclaim is SUPPORTED when the checker is not. That is not the only
disagreement. A method can also contradict a supported result, or abstain
when the checker found support.
"""

from follows_from.check import Verdict


def is_overclaim(method: Verdict, checker: Verdict) -> bool:
    return classify(method, checker) == "overclaim"


def classify(method: Verdict, checker: Verdict) -> str:
    if method is checker:
        return "agree"
    if method is Verdict.SUPPORTED and checker is not Verdict.SUPPORTED:
        return "overclaim"
    if method is Verdict.CONTRADICTED and checker is Verdict.SUPPORTED:
        return "false_contradiction"
    if method is Verdict.INSUFFICIENT_EVIDENCE and checker is Verdict.SUPPORTED:
        return "missed_support"
    return "other_disagreement"
