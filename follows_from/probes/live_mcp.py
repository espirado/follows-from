"""Call hosted lookup_mpfs. Stays out of check.py.

Python's urllib default User-Agent is Python-urllib/*, which Cloudflare
on api.rcintell.com rejects with Error 1010. Goose is not that client.
This caller sends an explicit User-Agent so the request reaches POST /v1/mcp.
"""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

from follows_from.check import Result, check

MCP_URL = "https://api.rcintell.com/v1/mcp"
# Signature Cloudflare already accepted on this host (initialize → 401, not 1010).
USER_AGENT = "goose/1.0"
PROTOCOL_VERSION = "2025-03-26"


class LiveMcpError(RuntimeError):
    """The HTTP layer failed before a tool result existed."""


def call_lookup_mpfs(code: str, api_key: str) -> dict[str, Any]:
    """POST tools/call lookup_mpfs. Returns the JSON-RPC result object."""
    body = json.dumps({
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/call",
        "params": {"name": "lookup_mpfs", "arguments": {"code": code}},
    }).encode()
    req = urllib.request.Request(
        MCP_URL,
        data=body,
        headers={
            "Content-Type": "application/json",
            "Accept": "application/json, text/event-stream",
            "User-Agent": USER_AGENT,
            "MCP-Protocol-Version": PROTOCOL_VERSION,
            "Mcp-Method": "tools/call",
            "Mcp-Name": "lookup_mpfs",
            "X-API-Key": api_key,
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            payload = json.loads(resp.read().decode())
    except urllib.error.HTTPError as exc:
        snippet = exc.read(400).decode(errors="replace")
        raise LiveMcpError(f"HTTP {exc.code}: {snippet[:300]}") from exc
    if "error" in payload:
        err = payload["error"]
        raise LiveMcpError(f"JSON-RPC {err.get('code')}: {err.get('message')}")
    result = payload.get("result")
    if not isinstance(result, dict):
        raise LiveMcpError("JSON-RPC result is missing")
    return result


def trace_from_call(code: str, result: dict[str, Any]) -> dict[str, Any]:
    """Trace whose grounds are the code we asked the tool for.

    The action claims the fee schedule returned that code. Echoing the
    payload's own ``hcpcs_code`` would make every hit ``SUPPORTED``.
    """
    return {
        "task": f"Quote the MPFS HCPCS code returned for {code}.",
        "source": {
            "server": "rci-knowledge",
            "host": "api.rcintell.com",
            "tool": "lookup_mpfs",
            "session": "live tools/call",
        },
        "steps": [
            {"type": "tool_call", "id": "c1", "name": "lookup_mpfs",
             "arguments": {"code": code}},
            {"type": "tool_result", "call_id": "c1",
             "isError": result.get("isError") is True,
             "structuredContent": result.get("structuredContent"),
             "content": result.get("content")},
            {"type": "action", "decision": f"quote_hcpcs_{code}",
             "grounds": [{"from": "c1", "field": "results.0.hcpcs_code",
                          "equals": code}]},
        ],
    }


def score_live_codes(codes: list[str], api_key: str | None = None) -> list[dict[str, Any]]:
    """Call lookup_mpfs once per code and score the returned HCPCS against the ask."""
    key = api_key if api_key is not None else load_api_key()
    if not key:
        raise LiveMcpError("no API key (set RCI_API_KEY or goose config X-API-Key)")
    rows = []
    for code in codes:
        result = call_lookup_mpfs(code, key)
        checked = check(trace_from_call(code, result))
        observed = _hcpcs(result)
        structured = result.get("structuredContent") if isinstance(result.get("structuredContent"), dict) else {}
        rows.append({
            "asked": code,
            "observed": observed,
            "total_count": structured.get("total_count") if structured else None,
            "isError": result.get("isError"),
            "verdict": checked.verdict.value,
            "reason": checked.findings[0].reason if checked.findings else checked.summary,
        })
    return rows


def check_live_lookup(code: str = "99213", api_key: str | None = None) -> Result:
    key = api_key if api_key is not None else load_api_key()
    if not key:
        raise LiveMcpError("no API key (set RCI_API_KEY or goose config X-API-Key)")
    result = call_lookup_mpfs(code, key)
    return check(trace_from_call(code, result))


def load_api_key() -> str | None:
    env = os.environ.get("RCI_API_KEY", "").strip()
    if env:
        return env
    cfg = Path.home() / ".config" / "goose" / "config.yaml"
    if not cfg.is_file():
        return None
    for line in cfg.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if stripped.startswith("X-API-Key:"):
            return stripped.split(":", 1)[1].strip() or None
    return None


def _hcpcs(result: dict[str, Any]) -> str | None:
    structured = result.get("structuredContent")
    if not isinstance(structured, dict):
        return None
    rows = structured.get("results")
    if not isinstance(rows, list) or not rows:
        return None
    first = rows[0]
    if not isinstance(first, dict):
        return None
    code = first.get("hcpcs_code")
    return str(code) if code else None
