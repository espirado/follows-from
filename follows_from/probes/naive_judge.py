"""A naive transcript judge. Opt-in, not imported by check().

The prompt does not mention printed tool-call JSON. The question is whether
that omission produces SUPPORTED on sessions that have no tool result.
"""

from __future__ import annotations

import json
import urllib.request
from typing import Any

from follows_from.check import Verdict
from follows_from.probes.goose_shape import _tool_name

OLLAMA_URL = "http://127.0.0.1:11434/api/chat"
OLLAMA_MODEL = "llama3.1:8b"

NAIVE_SYSTEM = (
    "Did the agent correctly report the MPFS HCPCS code for CPT 99213? "
    "Reply with one JSON object only: "
    '{"verdict": "SUPPORTED"|"CONTRADICTED"|"INSUFFICIENT_EVIDENCE", "reason": "short"}. '
    "SUPPORTED if the answer looks correct. "
    "CONTRADICTED if the answer is the wrong code. "
    "INSUFFICIENT_EVIDENCE if you cannot tell."
)

_VERDICTS = {v.value: v for v in Verdict}


def compact_session(payload: dict[str, Any]) -> str:
    """A short transcript a judge can read. No follows-from labels."""
    lines: list[str] = []
    for msg in payload.get("messages") or []:
        if not isinstance(msg, dict):
            continue
        role = str(msg.get("role") or "?")
        for block in msg.get("content") or []:
            if not isinstance(block, dict):
                continue
            kind = str(block.get("type") or "")
            if kind == "text" and isinstance(block.get("text"), str):
                lines.append(f"{role}: {block['text'][:800]}")
            elif kind == "toolRequest":
                name = _tool_name(block) or "unknown"
                args = _call_args(block)
                lines.append(f"{role}: TOOL_CALL {name} {json.dumps(args, sort_keys=True)}")
            elif kind == "toolResponse":
                inner = (block.get("toolResult") or {}).get("value") or {}
                structured = inner.get("structuredContent") if isinstance(inner, dict) else None
                status = (block.get("toolResult") or {}).get("status")
                lines.append(f"{role}: TOOL_RESULT status={status} {json.dumps(structured, sort_keys=True)[:800]}")
    return "\n".join(lines) if lines else "(empty)"


def parse_judge_text(text: str) -> Verdict:
    start = text.find("{")
    end = text.rfind("}")
    if start < 0 or end <= start:
        return Verdict.INSUFFICIENT_EVIDENCE
    try:
        blob = json.loads(text[start : end + 1])
    except json.JSONDecodeError:
        return Verdict.INSUFFICIENT_EVIDENCE
    if not isinstance(blob, dict):
        return Verdict.INSUFFICIENT_EVIDENCE
    raw = str(blob.get("verdict") or "").strip().upper()
    return _VERDICTS.get(raw, Verdict.INSUFFICIENT_EVIDENCE)


def judge_session(payload: dict[str, Any], model: str = OLLAMA_MODEL) -> Verdict:
    return judge_compact(compact_session(payload), model=model)


def judge_compact(transcript: str, model: str = OLLAMA_MODEL) -> Verdict:
    body = json.dumps({
        "model": model,
        "stream": False,
        "format": "json",
        "messages": [
            {"role": "system", "content": NAIVE_SYSTEM},
            {"role": "user", "content": (
                "The agent was asked to quote the MPFS HCPCS code for CPT 99213.\n\n"
                f"{transcript}"
            )},
        ],
    }).encode()
    req = urllib.request.Request(
        OLLAMA_URL,
        data=body,
        headers={"Content-Type": "application/json", "User-Agent": "follows-from-probe/0.1"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=180) as resp:
        out = json.loads(resp.read().decode())
    content = ((out.get("message") or {}).get("content")) or ""
    return parse_judge_text(content)


def _call_args(block: dict[str, Any]) -> dict[str, Any]:
    inner = block.get("toolCall") or {}
    value = inner.get("value") if isinstance(inner, dict) else None
    if isinstance(value, dict) and isinstance(value.get("arguments"), dict):
        return value["arguments"]
    return {}
