"""End-to-end: the mock MCP server's real results agree with the bundled traces.

Skipped unless the demo extra is installed: pip install -e ".[dev,demo]"
"""
import asyncio
import importlib.util
import json
import os

import pytest

pytest.importorskip("fastmcp")
from fastmcp import Client  # noqa: E402

from follows_from import Verdict, check  # noqa: E402

HERE = os.path.dirname(__file__)
ROOT = os.path.join(HERE, "..")
EXPECTED = {
    "supported.json": Verdict.SUPPORTED,
    "contradicted.json": Verdict.CONTRADICTED,
    "insufficient.json": Verdict.INSUFFICIENT_EVIDENCE,
}


def _server():
    path = os.path.join(ROOT, "goose", "mock_policy_server.py")
    spec = importlib.util.spec_from_file_location("mock_policy_server", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.mcp


def _live_result(arguments):
    async def call():
        async with Client(_server()) as client:
            return await client.call_tool("get_payer_policy", arguments,
                                          raise_on_error=False)
    r = asyncio.run(call())
    return {
        "isError": r.is_error,
        "structuredContent": r.structured_content,
        "content": [b.model_dump(exclude_none=True) for b in r.content],
    }


def _load(name):
    with open(os.path.join(ROOT, "examples", name), encoding="utf-8") as fh:
        return json.load(fh)


@pytest.mark.parametrize("name", sorted(EXPECTED))
def test_example_matches_live_mock_server(name):
    trace = _load(name)
    call = next(s for s in trace["steps"] if s["type"] == "tool_call")
    recorded = next(s for s in trace["steps"] if s["type"] == "tool_result")
    live = _live_result(call["arguments"])

    assert live["isError"] == recorded["isError"]
    if not live["isError"]:
        assert live["structuredContent"] == recorded["structuredContent"]


@pytest.mark.parametrize("name", sorted(EXPECTED))
def test_live_result_yields_expected_verdict(name):
    trace = _load(name)
    call = next(s for s in trace["steps"] if s["type"] == "tool_call")
    action = next(s for s in trace["steps"] if s["type"] == "action")
    live = {"type": "tool_result", "call_id": call["id"], **_live_result(call["arguments"])}

    assert check({"steps": [call, live, action]}).verdict is EXPECTED[name]
