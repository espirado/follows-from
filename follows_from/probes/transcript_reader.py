"""A stand-in for the verifier that reads the chat instead of the MCP trace.

It treats a printed tool-call JSON as if the call ran and the arguments came
back as the result. That is the mislabel. It is not part of ``check``.
"""

from __future__ import annotations

import json
from typing import Any

from follows_from.check import Verdict


def read_printed_call(text: str, claimed: str | None = None) -> Verdict:
    """Return SUPPORTED when a printed lookup_mpfs code matches the claim.

    The printed parameter is taken as the evidence. There is no tool result
    to consult. With ``claimed`` set, the parameter has to equal that value;
    a printed call for a different code is not treated as support.
    """
    blob = _first_object(text)
    if blob is None:
        return Verdict.INSUFFICIENT_EVIDENCE
    name = str(blob.get("name") or "")
    params = blob.get("parameters")
    if "lookup_mpfs" not in name or not isinstance(params, dict):
        return Verdict.INSUFFICIENT_EVIDENCE
    code = params.get("code")
    if not code:
        return Verdict.INSUFFICIENT_EVIDENCE
    if claimed is not None and str(code) != claimed:
        return Verdict.INSUFFICIENT_EVIDENCE
    return Verdict.SUPPORTED


def _first_object(text: str) -> dict[str, Any] | None:
    start = text.find("{")
    end = text.rfind("}")
    if start < 0 or end <= start:
        return None
    try:
        blob = json.loads(text[start : end + 1])
    except json.JSONDecodeError:
        return None
    return blob if isinstance(blob, dict) else None
