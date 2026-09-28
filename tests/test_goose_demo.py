"""Smoke test for the optional mock MCP server.

The bundled examples are captured from production rci-knowledge (`lookup_mpfs`),
not from this mock. This file only checks that the mock still starts and returns
deterministic coverage data if you install the demo extra.
"""
import asyncio
import importlib.util
import os

import pytest

pytest.importorskip("fastmcp")
from fastmcp import Client  # noqa: E402

HERE = os.path.dirname(__file__)


def _server():
    path = os.path.join(HERE, "..", "goose", "mock_policy_server.py")
    spec = importlib.util.spec_from_file_location("mock_policy_server", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.mcp


def _call(claim_id: str):
    async def run():
        async with Client(_server()) as client:
            return await client.call_tool(
                "get_payer_policy",
                {"claim_id": claim_id, "procedure": "X123"},
                raise_on_error=False,
            )
    return asyncio.run(run())


def test_mock_covered_and_uncovered_and_outage():
    ok = _call("CLM-1001")
    assert ok.is_error is False
    assert ok.structured_content["covered"] is True

    denied = _call("CLM-1002")
    assert denied.is_error is False
    assert denied.structured_content["covered"] is False

    down = _call("CLM-1003")
    assert down.is_error is True
