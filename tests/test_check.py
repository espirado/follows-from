"""Tests for the follows-from checker. Run: python -m pytest -q"""
import json
import os
import subprocess
import sys

from follows_from import Verdict, check

HERE = os.path.dirname(__file__)
EX = os.path.join(HERE, "..", "examples")


def _load(name):
    with open(os.path.join(EX, name), encoding="utf-8") as fh:
        return json.load(fh)


def test_supported_example():
    assert check(_load("supported.json")).verdict is Verdict.SUPPORTED


def test_contradicted_example():
    r = check(_load("contradicted.json"))
    assert r.verdict is Verdict.CONTRADICTED
    assert r.findings[0].observed is False and r.findings[0].expected is True


def test_insufficient_example():
    assert check(_load("insufficient.json")).verdict is Verdict.INSUFFICIENT_EVIDENCE


def test_ungrounded_action_is_insufficient():
    trace = {"steps": [
        {"type": "tool_result", "call_id": "c1", "ok": True, "content": {"covered": True}},
        {"type": "action", "decision": "approve_claim"},
    ]}
    assert check(trace).verdict is Verdict.INSUFFICIENT_EVIDENCE


def test_no_action_is_insufficient():
    trace = {"steps": [
        {"type": "tool_result", "call_id": "c1", "ok": True, "content": {"covered": True}},
    ]}
    assert check(trace).verdict is Verdict.INSUFFICIENT_EVIDENCE


def test_missing_field_is_insufficient():
    trace = {"steps": [
        {"type": "tool_result", "call_id": "c1", "ok": True, "content": {"other": 1}},
        {"type": "action", "decision": "approve_claim",
         "grounds": [{"from": "c1", "field": "covered", "equals": True}]},
    ]}
    assert check(trace).verdict is Verdict.INSUFFICIENT_EVIDENCE


def test_all_of_contradiction_dominates_a_match():
    # one premise matches, one is contradicted -> overall CONTRADICTED
    trace = {"steps": [
        {"type": "tool_result", "call_id": "c1", "ok": True,
         "content": {"covered": True, "in_network": False}},
        {"type": "action", "decision": "approve_claim", "grounds": {"all_of": [
            {"from": "c1", "field": "covered", "equals": True},
            {"from": "c1", "field": "in_network", "equals": True},
        ]}},
    ]}
    assert check(trace).verdict is Verdict.CONTRADICTED


def test_any_of_one_match_supports():
    trace = {"steps": [
        {"type": "tool_result", "call_id": "c1", "ok": True,
         "content": {"covered": False, "prior_auth": True}},
        {"type": "action", "decision": "approve_claim", "grounds": {"any_of": [
            {"from": "c1", "field": "covered", "equals": True},
            {"from": "c1", "field": "prior_auth", "equals": True},
        ]}},
    ]}
    assert check(trace).verdict is Verdict.SUPPORTED


def test_exists_operator():
    trace = {"steps": [
        {"type": "tool_result", "call_id": "c1", "ok": True, "content": {"denial_code": "CO-50"}},
        {"type": "action", "decision": "deny_claim",
         "grounds": [{"from": "c1", "field": "denial_code", "exists": True}]},
    ]}
    assert check(trace).verdict is Verdict.SUPPORTED


# --- MCP CallToolResult shape --------------------------------------------------

APPROVE_IF_COVERED = [{"from": "c1", "field": "covered", "equals": True}]


def _with_result(result, grounds=APPROVE_IF_COVERED):
    return {"steps": [
        {"type": "tool_result", "call_id": "c1", **result},
        {"type": "action", "decision": "approve_claim", "grounds": grounds},
    ]}


def test_mcp_structured_content_is_the_evidence():
    r = check(_with_result({"isError": False, "structuredContent": {"covered": False}}))
    assert r.verdict is Verdict.CONTRADICTED


def test_mcp_is_error_is_insufficient():
    r = check(_with_result({"isError": True, "structuredContent": {"covered": True},
                            "content": [{"type": "text", "text": "boom"}]}))
    assert r.verdict is Verdict.INSUFFICIENT_EVIDENCE
    assert "failed" in r.findings[0].reason


def test_mcp_single_json_text_block_is_the_evidence():
    r = check(_with_result({"isError": False,
                            "content": [{"type": "text", "text": '{"covered": true}'}]}))
    assert r.verdict is Verdict.SUPPORTED


def test_mcp_prose_text_block_is_insufficient():
    r = check(_with_result({"isError": False,
                            "content": [{"type": "text", "text": "Covered: yes"}]}))
    assert r.verdict is Verdict.INSUFFICIENT_EVIDENCE
    assert "no structured fields" in r.findings[0].reason


def test_unstructured_result_does_not_satisfy_exists_false():
    grounds = [{"from": "c1", "field": "denial_code", "exists": False}]
    r = check(_with_result({"content": [{"type": "text", "text": "ok"}]}, grounds))
    assert r.verdict is Verdict.INSUFFICIENT_EVIDENCE


# --- JSON-strict comparison --------------------------------------------------


def test_one_is_not_true():
    r = check(_with_result({"structuredContent": {"covered": 1}}))
    assert r.verdict is Verdict.CONTRADICTED
    assert r.findings[0].observed == 1 and r.findings[0].expected is True


def test_zero_is_not_false_under_not_equals():
    grounds = [{"from": "c1", "field": "covered", "not_equals": False}]
    assert check(_with_result({"structuredContent": {"covered": 0}}, grounds)).verdict \
        is Verdict.SUPPORTED


def test_in_uses_json_equality():
    grounds = [{"from": "c1", "field": "tier", "in": [True, "gold"]}]
    assert check(_with_result({"structuredContent": {"tier": 1}}, grounds)).verdict \
        is Verdict.CONTRADICTED


def test_integer_and_float_are_the_same_json_number():
    grounds = [{"from": "c1", "field": "copay", "equals": 20}]
    assert check(_with_result({"structuredContent": {"copay": 20.0}}, grounds)).verdict \
        is Verdict.SUPPORTED


# --- malformed premises are unverifiable, not silently resolved ---------------


def test_in_with_a_string_is_malformed_not_substring_match():
    grounds = [{"from": "c1", "field": "status", "in": "approved_later"}]
    r = check(_with_result({"structuredContent": {"status": "approved"}}, grounds))
    assert r.verdict is Verdict.INSUFFICIENT_EVIDENCE


def test_two_operators_is_malformed():
    grounds = [{"from": "c1", "field": "covered", "equals": False, "exists": True}]
    r = check(_with_result({"structuredContent": {"covered": True}}, grounds))
    assert r.verdict is Verdict.INSUFFICIENT_EVIDENCE
    assert "2 operators" in r.findings[0].reason


def test_single_unwrapped_premise_is_checked():
    r = check(_with_result({"structuredContent": {"covered": False}},
                           APPROVE_IF_COVERED[0]))
    assert r.verdict is Verdict.CONTRADICTED


# --- every verdict carries a Finding -----------------------------------------


def test_every_verdict_has_a_finding():
    traces = [
        {"steps": []},
        {"steps": "not a list"},
        _with_result({"structuredContent": {"covered": True}}, []),
        _with_result({"structuredContent": {"covered": True}}, {"all_of": []}),
        _with_result({"structuredContent": {"covered": True}}, {"nonsense": 1}),
        _with_result({"structuredContent": {"covered": True}}, "covered"),
        _with_result({"structuredContent": {"covered": True}}, ["not a premise"]),
    ]
    for trace in traces:
        r = check(trace)
        assert r.verdict is Verdict.INSUFFICIENT_EVIDENCE, trace
        assert r.findings, trace


# --- CLI exit codes ----------------------------------------------------------


def _cli(*args):
    return subprocess.run([sys.executable, "-m", "follows_from", *args],
                          capture_output=True, text=True).returncode


def test_cli_exit_codes_match_verdicts():
    assert _cli(os.path.join(EX, "supported.json")) == 0
    assert _cli(os.path.join(EX, "contradicted.json")) == 1
    assert _cli(os.path.join(EX, "insufficient.json")) == 2


def test_cli_failure_to_run_is_not_a_verdict(tmp_path):
    bad = tmp_path / "bad.json"
    bad.write_text("{not json")
    array = tmp_path / "array.json"
    array.write_text("[]")
    assert _cli() == 3
    assert _cli(str(tmp_path / "missing.json")) == 3
    assert _cli(str(bad)) == 3
    assert _cli(str(array)) == 3


# --- nested field paths ------------------------------------------------------


def test_dotted_path_reads_nested_object_and_array():
    payload = {"results": [{"hcpcs_code": "99213", "work_rvu": 1.3}], "total_count": 1}
    grounds = [{"from": "c1", "field": "results.0.hcpcs_code", "equals": "99213"}]
    r = check(_with_result({"structuredContent": payload}, grounds))
    assert r.verdict is Verdict.SUPPORTED
    assert r.findings[0].observed == "99213"


def test_bare_field_still_means_top_level():
    payload = {"results": [{"hcpcs_code": "99213"}], "total_count": 1}
    r = check(_with_result({"structuredContent": payload},
                           [{"from": "c1", "field": "hcpcs_code", "equals": "99213"}]))
    assert r.verdict is Verdict.INSUFFICIENT_EVIDENCE


def test_missing_nested_path_is_insufficient():
    payload = {"results": [{"hcpcs_code": "99213"}]}
    r = check(_with_result({"structuredContent": payload},
                           [{"from": "c1", "field": "results.1.hcpcs_code", "equals": "99213"}]))
    assert r.verdict is Verdict.INSUFFICIENT_EVIDENCE


def test_nested_value_can_contradict():
    payload = {"results": [{"hcpcs_code": "99214"}]}
    r = check(_with_result({"structuredContent": payload},
                           [{"from": "c1", "field": "results.0.hcpcs_code", "equals": "99213"}]))
    assert r.verdict is Verdict.CONTRADICTED
    assert r.findings[0].observed == "99214"


def test_malformed_path_is_insufficient():
    r = check(_with_result({"structuredContent": {"a": {"b": 1}}},
                           [{"from": "c1", "field": "a..b", "equals": 1}]))
    assert r.verdict is Verdict.INSUFFICIENT_EVIDENCE
    assert "malformed" in r.findings[0].reason


def test_nested_exists():
    payload = {"results": [{"hcpcs_code": "99213"}]}
    r = check(_with_result({"structuredContent": payload},
                           [{"from": "c1", "field": "results.0.hcpcs_code", "exists": True}]))
    assert r.verdict is Verdict.SUPPORTED

