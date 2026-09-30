"""The printed-call pair: a transcript reader and the trace checker disagree
only when the tool never ran."""
import os

from follows_from import Verdict, check
from follows_from.probes.transcript_reader import read_printed_call

HERE = os.path.dirname(__file__)
EX = os.path.join(HERE, "..", "examples")

PRINTED = '{"name": "rci-knowledge__lookup_mpfs", "parameters": {"code": "99213"}}'


def _load(name):
    import json
    with open(os.path.join(EX, name), encoding="utf-8") as fh:
        return json.load(fh)


def test_unexecuted_arm_is_the_disagreement():
    trace_verdict = check(_load("unexecuted.json")).verdict
    chat_verdict = read_printed_call(PRINTED)
    assert trace_verdict is Verdict.INSUFFICIENT_EVIDENCE
    assert chat_verdict is Verdict.SUPPORTED


def test_executed_arm_both_say_supported():
    trace_verdict = check(_load("supported.json")).verdict
    chat_verdict = read_printed_call(PRINTED)
    assert trace_verdict is Verdict.SUPPORTED
    assert chat_verdict is Verdict.SUPPORTED


def test_prose_without_a_call_is_insufficient_for_the_reader():
    assert read_printed_call("I will look that up later.") is Verdict.INSUFFICIENT_EVIDENCE


def test_printed_code_that_is_not_the_claim_is_not_support():
    assert read_printed_call(PRINTED, claimed="99214") is Verdict.INSUFFICIENT_EVIDENCE
