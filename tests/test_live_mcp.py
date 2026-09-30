"""The live MCP caller must not send Python's default User-Agent."""
from unittest.mock import patch

from follows_from.probes.live_mcp import USER_AGENT, call_lookup_mpfs, trace_from_call


def test_tools_call_sets_goose_user_agent():
    captured = {}

    class _Resp:
        def read(self):
            return b'{"jsonrpc":"2.0","id":1,"result":{"isError":false,"structuredContent":{"results":[{"hcpcs_code":"99213"}],"total_count":1}}}'

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

    def fake_urlopen(req, timeout=60):
        captured["ua"] = req.get_header("User-agent") or req.get_header("User-Agent")
        captured["url"] = req.full_url
        return _Resp()

    with patch("follows_from.probes.live_mcp.urllib.request.urlopen", fake_urlopen):
        result = call_lookup_mpfs("99213", "kp_live_dummy")
    assert captured["ua"] == USER_AGENT
    assert captured["ua"] != "Python-urllib/3.12"
    assert captured["url"] == "https://api.rcintell.com/v1/mcp"
    assert result["structuredContent"]["results"][0]["hcpcs_code"] == "99213"


def test_trace_from_call_uses_the_returned_code():
    result = {
        "isError": False,
        "structuredContent": {"results": [{"hcpcs_code": "99213"}], "total_count": 1},
    }
    trace = trace_from_call("99213", result)
    assert trace["steps"][0]["arguments"]["code"] == "99213"
    assert trace["steps"][1]["structuredContent"]["results"][0]["hcpcs_code"] == "99213"
    assert trace["steps"][2]["grounds"][0]["equals"] == "99213"


def test_grounds_are_the_asked_code_not_the_payload_echo():
    result = {
        "isError": False,
        "structuredContent": {"results": [{"hcpcs_code": "99214"}], "total_count": 1},
    }
    trace = trace_from_call("99213", result)
    assert trace["steps"][2]["grounds"][0]["equals"] == "99213"
