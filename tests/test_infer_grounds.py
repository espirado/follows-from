"""Grounds copied from the tool-call argument, scored by the checker."""
from pathlib import Path

from follows_from import Verdict
from follows_from.probes.infer_grounds import score_inferred_grounds

EX = Path(__file__).resolve().parents[1] / "examples"


def _by_factor():
    return {row.factor: row for row in score_inferred_grounds(EX)}


def test_overclaim_is_a_claim_other_than_the_argument():
    rows = _by_factor()
    over = [name for name, row in rows.items() if row.overclaim]
    assert over == ["claim_99214", "claim_99215"]
    for name in over:
        assert rows[name].reference is Verdict.CONTRADICTED
        assert rows[name].inferred is Verdict.SUPPORTED
        assert rows[name].inferred_equals == "99213"
        assert rows[name].captured is False


def test_executed_control_copies_the_argument_and_agrees():
    row = _by_factor()["none"]
    assert row.reference is Verdict.SUPPORTED
    assert row.inferred is Verdict.SUPPORTED
    assert row.inferred_equals == "99213"
    assert row.captured is True
    assert row.overclaim is False


def test_a_missing_or_failed_result_stays_insufficient():
    rows = _by_factor()
    for name in ("drop_tool_result", "mark_is_error"):
        assert rows[name].reference is Verdict.INSUFFICIENT_EVIDENCE
        assert rows[name].inferred is Verdict.INSUFFICIENT_EVIDENCE
        assert rows[name].inferred_equals == "99213"
        assert rows[name].overclaim is False


def test_a_different_result_is_contradicted_for_both():
    row = _by_factor()["change_result_code"]
    assert row.reference is Verdict.CONTRADICTED
    assert row.inferred is Verdict.CONTRADICTED
    assert row.overclaim is False


def test_without_a_tool_call_the_inferrer_abstains():
    row = _by_factor()["drop_tool_call"]
    assert row.reference is Verdict.SUPPORTED
    assert row.inferred is Verdict.INSUFFICIENT_EVIDENCE
    assert row.inferred_equals is None
    assert row.overclaim is False
