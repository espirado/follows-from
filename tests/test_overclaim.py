"""Disagreement labels relative to the checker."""
from follows_from import Verdict
from follows_from.probes.overclaim import classify, is_overclaim


def test_overclaim_is_supported_when_the_checker_is_not():
    assert is_overclaim(Verdict.SUPPORTED, Verdict.INSUFFICIENT_EVIDENCE)
    assert classify(Verdict.SUPPORTED, Verdict.INSUFFICIENT_EVIDENCE) == "overclaim"
    assert classify(Verdict.SUPPORTED, Verdict.CONTRADICTED) == "overclaim"


def test_false_contradiction_and_missed_support():
    assert classify(Verdict.CONTRADICTED, Verdict.SUPPORTED) == "false_contradiction"
    assert classify(Verdict.INSUFFICIENT_EVIDENCE, Verdict.SUPPORTED) == "missed_support"
    assert is_overclaim(Verdict.CONTRADICTED, Verdict.SUPPORTED) is False


def test_matching_verdicts_agree():
    assert classify(Verdict.SUPPORTED, Verdict.SUPPORTED) == "agree"
    assert classify(Verdict.INSUFFICIENT_EVIDENCE, Verdict.INSUFFICIENT_EVIDENCE) == "agree"
