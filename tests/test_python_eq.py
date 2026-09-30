"""Python == against the current checker, on bool/int pairs.

Rows are keyed by type and value. Python hashes ``1`` and ``True`` together,
so a dict of bare values would collapse the class into the control.
"""
from follows_from import Verdict
from follows_from.probes.python_eq import score_python_eq


def _sig(observed, expected):
    return (type(observed).__name__, observed, type(expected).__name__, expected)


def _rows():
    return {_sig(row.observed, row.expected): row for row in score_python_eq()}


def test_bool_int_collisions_are_the_overclaim_class():
    rows = _rows()
    over = [sig for sig, row in rows.items() if row.overclaim]
    assert over == [
        ("int", 1, "bool", True),
        ("bool", True, "int", 1),
        ("int", 0, "bool", False),
        ("bool", False, "int", 0),
    ]
    for sig in over:
        assert rows[sig].python_eq is Verdict.SUPPORTED
        assert rows[sig].checker is Verdict.CONTRADICTED


def test_matching_values_are_not_the_class():
    rows = _rows()
    for sig in (
        ("bool", True, "bool", True),
        ("int", 1, "int", 1),
        ("int", 20, "float", 20.0),
    ):
        assert rows[sig].checker is Verdict.SUPPORTED
        assert rows[sig].python_eq is Verdict.SUPPORTED
        assert rows[sig].overclaim is False


def test_a_non_colliding_mismatch_is_not_an_overclaim():
    row = _rows()[("int", 2, "bool", True)]
    assert row.python_eq is Verdict.CONTRADICTED
    assert row.checker is Verdict.CONTRADICTED
    assert row.overclaim is False
