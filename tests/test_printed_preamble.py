"""Printed-only compact transcripts used in the preamble factor."""
from follows_from.probes.printed_preamble import (
    PREAMBLE_CALL,
    PREAMBLE_RESPONSE,
    JSON_LONG,
    JSON_SHORT,
    printed_only_transcript,
)


def test_session_one_is_call_plus_short_json():
    text = printed_only_transcript(PREAMBLE_CALL, JSON_SHORT)
    assert "function call with its proper arguments" in text
    assert '"year"' not in JSON_SHORT
    assert "TOOL_RESULT" not in text


def test_session_four_is_response_plus_long_json():
    text = printed_only_transcript(PREAMBLE_RESPONSE, JSON_LONG)
    assert "JSON response" in text
    assert "2026" in JSON_LONG
