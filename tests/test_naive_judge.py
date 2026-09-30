"""Naive judge compact/parse. Does not call ollama."""
from follows_from import Verdict
from follows_from.probes.naive_judge import compact_session, parse_judge_text


def test_parse_reads_a_verdict_object():
    assert parse_judge_text('{"verdict": "SUPPORTED", "reason": "ok"}') is Verdict.SUPPORTED
    assert parse_judge_text('noise {"verdict": "CONTRADICTED"}') is Verdict.CONTRADICTED


def test_parse_garbage_is_insufficient():
    assert parse_judge_text("I think it worked.") is Verdict.INSUFFICIENT_EVIDENCE


def test_compact_keeps_a_printed_call_and_has_no_tool_result():
    payload = {
        "messages": [
            {"role": "user", "content": [{"type": "text", "text": "look up 99213"}]},
            {"role": "assistant", "content": [{"type": "text", "text": '{"name": "rci-knowledge__lookup_mpfs", "parameters": {"code": "99213"}}'}]},
        ]
    }
    text = compact_session(payload)
    assert "lookup_mpfs" in text
    assert "TOOL_RESULT" not in text


def test_compact_keeps_a_tool_result():
    payload = {
        "messages": [
            {"role": "assistant", "content": [{"type": "toolRequest", "toolCall": {"value": {"name": "lookup_mpfs", "arguments": {"code": "99213"}}}}]},
            {"role": "user", "content": [{"type": "toolResponse", "toolResult": {"status": "success", "value": {"structuredContent": {"results": [{"hcpcs_code": "99213"}]}}}}]},
        ]
    }
    text = compact_session(payload)
    assert "TOOL_CALL" in text
    assert "TOOL_RESULT" in text
    assert "99213" in text
