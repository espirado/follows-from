"""Classify a goose ``run --output-format json`` payload.

Does not call ``check``. The labels are about what the session contained:
a real tool result, a printed call, or neither.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Any

from follows_from.probes.transcript_reader import _first_object

_CODE = re.compile(r"\b(\d{5})\b")


@dataclass(frozen=True)
class GooseShape:
    label: str
    printed_call: dict[str, Any] | None
    quoted_codes: tuple[str, ...]
    tool_call_names: tuple[str, ...]
    n_assistant: int


def classify_goose_json(payload: dict[str, Any]) -> GooseShape:
    messages = payload.get("messages") or []
    printed = None
    quoted: list[str] = []
    tool_names: list[str] = []
    n_assistant = 0
    for msg in messages:
        if not isinstance(msg, dict):
            continue
        role = msg.get("role")
        if role == "assistant":
            n_assistant += 1
        for block in msg.get("content") or []:
            if not isinstance(block, dict):
                continue
            name = _tool_name(block)
            if name:
                tool_names.append(name)
            text = block.get("text")
            if not isinstance(text, str):
                continue
            blob = _first_object(text)
            if blob and "lookup_mpfs" in str(blob.get("name") or ""):
                printed = blob
            if role == "assistant":
                quoted.extend(_CODE.findall(text))
    if tool_names:
        label = "executed"
    elif printed is not None:
        label = "printed_only"
    elif quoted:
        label = "quoted_without_call"
    else:
        label = "no_code"
    return GooseShape(
        label=label,
        printed_call=printed,
        quoted_codes=tuple(quoted),
        tool_call_names=tuple(tool_names),
        n_assistant=n_assistant,
    )


def _tool_name(block: dict[str, Any]) -> str | None:
    for key in ("name", "toolName", "tool_name"):
        if block.get(key):
            return str(block[key])
    for wrapper_key in ("toolCall", "tool_call", "toolResult", "tool_result"):
        inner = block.get(wrapper_key)
        if not isinstance(inner, dict):
            continue
        value = inner.get("value")
        if isinstance(value, dict) and value.get("name"):
            return str(value["name"])
        if inner.get("name"):
            return str(inner["name"])
    return None


def mcp_result_from_goose(payload: dict[str, Any]) -> dict[str, Any] | None:
    """structuredContent from a goose toolResponse, if present."""
    for msg in payload.get("messages") or []:
        if not isinstance(msg, dict):
            continue
        for block in msg.get("content") or []:
            if not isinstance(block, dict) or block.get("type") != "toolResponse":
                continue
            inner = block.get("toolResult") or {}
            value = inner.get("value") if isinstance(inner, dict) else None
            if not isinstance(value, dict):
                continue
            structured = value.get("structuredContent")
            if isinstance(structured, dict):
                failed = inner.get("status") == "error" or value.get("isError") is True
                return {
                    "isError": failed,
                    "structuredContent": structured,
                    "content": value.get("content"),
                }
    return None


def load_payload(text: str) -> dict[str, Any]:
    """goose prints a banner, then one JSON object."""
    start = text.find("{")
    if start < 0:
        raise ValueError("no JSON object in goose output")
    return json.loads(text[start:])
