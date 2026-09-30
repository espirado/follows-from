"""Classify goose --output-format json without calling the model."""
import json

from follows_from.probes.goose_shape import classify_goose_json, load_payload

PRINTED_ONLY = {
    "messages": [
        {"role": "user", "content": [{"type": "text", "text": "look up 99213"}]},
        {"role": "assistant", "content": [{
            "type": "text",
            "text": 'Here is the request:\n{"name": "rci-knowledge__lookup_mpfs", "parameters": {"code": "99213"}}',
        }]},
    ]
}

EXECUTED = {
    "messages": [
        {"role": "user", "content": [{"type": "text", "text": "look up 99213"}]},
        {"role": "assistant", "content": [
            {"type": "toolRequest", "name": "lookup_mpfs"},
            {"type": "text", "text": "The HCPCS code is 99213."},
        ]},
        {"role": "user", "content": [{"type": "toolResponse", "name": "lookup_mpfs"}]},
    ]
}


def test_printed_json_without_a_tool_block_is_printed_only():
    shape = classify_goose_json(PRINTED_ONLY)
    assert shape.label == "printed_only"
    assert shape.printed_call["parameters"]["code"] == "99213"
    assert shape.tool_call_names == ()


def test_a_tool_request_block_is_executed():
    shape = classify_goose_json(EXECUTED)
    assert shape.label == "executed"
    assert "lookup_mpfs" in shape.tool_call_names


def test_goose_nested_tool_call_value_is_executed():
    payload = {
        "messages": [{
            "role": "assistant",
            "content": [{
                "type": "toolRequest",
                "toolCall": {"status": "success", "value": {"name": "rci-knowledge__lookup_mpfs", "arguments": {"code": "99213"}}},
            }],
        }]
    }
    shape = classify_goose_json(payload)
    assert shape.label == "executed"
    assert any("lookup_mpfs" in n for n in shape.tool_call_names)


def test_load_payload_skips_the_goose_banner():
    blob = "banner\n" + json.dumps(PRINTED_ONLY)
    assert load_payload(blob)["messages"][0]["role"] == "user"
