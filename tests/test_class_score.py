"""The printed-call class: one gesture, traces that differ in the evidence."""
from pathlib import Path

from follows_from import Verdict
from follows_from.probes.class_score import score_printed_call_class

EX = Path(__file__).resolve().parents[1] / "examples"


def _by_shape():
    return {row.shape: row for row in score_printed_call_class(EX)}


def test_overclaim_is_the_echo_when_the_trace_does_not_support():
    rows = _by_shape()
    over = {name for name, row in rows.items() if row.overclaim}
    assert over == {"unexecuted", "tool_error", "result_disagrees"}


def test_each_overclaim_has_the_checker_verdict_for_that_shape():
    rows = _by_shape()
    assert rows["unexecuted"].trace is Verdict.INSUFFICIENT_EVIDENCE
    assert rows["tool_error"].trace is Verdict.INSUFFICIENT_EVIDENCE
    assert rows["result_disagrees"].trace is Verdict.CONTRADICTED
    for name in ("unexecuted", "tool_error", "result_disagrees"):
        assert rows[name].reader is Verdict.SUPPORTED


def test_executed_control_is_not_an_overclaim():
    row = _by_shape()["executed"]
    assert row.trace is Verdict.SUPPORTED
    assert row.reader is Verdict.SUPPORTED
    assert row.overclaim is False
    assert row.captured is True


def test_a_claim_the_print_does_not_echo_is_outside_the_class():
    row = _by_shape()["claim_disagrees"]
    assert row.trace is Verdict.CONTRADICTED
    assert row.reader is Verdict.INSUFFICIENT_EVIDENCE
    assert row.overclaim is False


def test_only_the_disagreement_row_is_constructed():
    rows = _by_shape()
    assert rows["result_disagrees"].captured is False
    assert all(rows[name].captured for name in ("executed", "unexecuted", "tool_error", "claim_disagrees"))
