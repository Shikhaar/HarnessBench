"""Token extraction and aggregation from provider wire traffic."""

import json
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field


class TokenRecord(BaseModel):
    """Token usage metrics captured from an individual API call."""
    model: str = ""
    input_tokens: int = 0
    output_tokens: int = 0
    cache_read_tokens: int = 0
    cache_write_tokens: int = 0
    provider_reported: bool = False
    status_code: int = 200
    latency_seconds: float = 0.0


class ApiUsageSummary(BaseModel):
    """Aggregated token usage across all API requests in a session."""
    total_requests: int = 0
    input_tokens: int = 0
    output_tokens: int = 0
    cache_read_tokens: int = 0
    cache_write_tokens: int = 0
    total_tokens: int = 0
    total_latency_seconds: float = 0.0

    def add(self, record: TokenRecord) -> None:
        self.total_requests += 1
        self.input_tokens += record.input_tokens
        self.output_tokens += record.output_tokens
        self.cache_read_tokens += record.cache_read_tokens
        self.cache_write_tokens += record.cache_write_tokens
        self.total_tokens = self.input_tokens + self.output_tokens
        self.total_latency_seconds += record.latency_seconds


def parse_anthropic_json_usage(data: Dict[str, Any]) -> TokenRecord:
    """Extract usage from standard Anthropic messages response JSON."""
    model = data.get("model", "")
    usage = data.get("usage", {})

    if not usage:
        return TokenRecord(model=model, provider_reported=False)

    return TokenRecord(
        model=model,
        input_tokens=usage.get("input_tokens", 0),
        output_tokens=usage.get("output_tokens", 0),
        cache_read_tokens=usage.get("cache_read_input_tokens", 0),
        cache_write_tokens=usage.get("cache_creation_input_tokens", 0),
        provider_reported=True,
    )


def parse_anthropic_sse_event(event_line: str, data_line: str) -> Dict[str, Any]:
    """Parse an SSE event and return any usage delta discovered."""
    parsed: Dict[str, Any] = {}
    if not data_line.startswith("data:"):
        return parsed

    payload_str = data_line[len("data:"):].strip()
    if not payload_str or payload_str == "[DONE]":
        return parsed

    try:
        data = json.loads(payload_str)
    except Exception:
        return parsed

    # Check for message_start
    if data.get("type") == "message_start":
        msg = data.get("message", {})
        parsed["model"] = msg.get("model", "")
        usage = msg.get("usage", {})
        parsed["input_tokens"] = usage.get("input_tokens", 0)
        parsed["cache_read_tokens"] = usage.get("cache_read_input_tokens", 0)
        parsed["cache_write_tokens"] = usage.get("cache_creation_input_tokens", 0)

    # Check for message_delta (final usage)
    elif data.get("type") == "message_delta":
        usage = data.get("usage", {})
        if "output_tokens" in usage:
            parsed["output_tokens"] = usage.get("output_tokens", 0)

    return parsed
