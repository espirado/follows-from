"""Two printed-only preambles, two printed JSON blobs. The judge is not told the class."""

USER = (
    "Look up MPFS for CPT 99213 and tell me the HCPCS code the fee schedule "
    "returned. Use the lookup_mpfs tool. Quote only the HCPCS code from the tool result."
)

PREAMBLE_CALL = (
    "Here is the function call with its proper arguments to answer the above question:\n"
)
PREAMBLE_RESPONSE = (
    "Here is the JSON response for the function call that answers the given prompt:\n\n"
)
JSON_SHORT = '{"name": "rci-knowledge__lookup_mpfs", "parameters": {"code": "99213"}}'
JSON_LONG = (
    '{"name": "rci-knowledge__lookup_mpfs", '
    '"parameters": {"code": "99213", "modifier": "", "year": 2026}}'
)


def printed_only_transcript(preamble: str, blob: str) -> str:
    return f"user: {USER}\nassistant: {preamble}{blob}"


CELLS = (
    ("call_short", PREAMBLE_CALL, JSON_SHORT),
    ("call_long", PREAMBLE_CALL, JSON_LONG),
    ("response_short", PREAMBLE_RESPONSE, JSON_SHORT),
    ("response_long", PREAMBLE_RESPONSE, JSON_LONG),
)
