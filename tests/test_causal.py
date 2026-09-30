"""One edit at a time, starting from the executed capture."""
from pathlib import Path

from follows_from import Verdict
from follows_from.probes.causal import score_mutations

EX = Path(__file__).resolve().parents[1] / "examples"


def _by_factor():
    return {row.factor: row for row in score_mutations(EX)}


def test_overclaim_factors_are_the_ones_that_remove_trace_support():
    rows = _by_factor()
    over = {name for name, row in rows.items() if row.overclaim}
    assert over == {"drop_tool_result", "mark_is_error", "change_result_code"}


def test_control_and_unrelated_edit_stay_supported():
    rows = _by_factor()
    for name in ("none", "change_descriptor"):
        assert rows[name].checker is Verdict.SUPPORTED
        assert rows[name].reader is Verdict.SUPPORTED
        assert rows[name].overclaim is False


def test_changing_the_claim_leaves_the_class():
    row = _by_factor()["change_claim"]
    assert row.checker is Verdict.CONTRADICTED
    assert row.reader is Verdict.INSUFFICIENT_EVIDENCE
    assert row.overclaim is False


def test_each_removing_edit_has_its_own_checker_verdict():
    rows = _by_factor()
    assert rows["drop_tool_result"].checker is Verdict.INSUFFICIENT_EVIDENCE
    assert rows["mark_is_error"].checker is Verdict.INSUFFICIENT_EVIDENCE
    assert rows["change_result_code"].checker is Verdict.CONTRADICTED
    for name in ("drop_tool_result", "mark_is_error", "change_result_code"):
        assert rows[name].reader is Verdict.SUPPORTED
