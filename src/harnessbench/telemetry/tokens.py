"""Token extraction and aggregation from provider wire traffic across Anthropic and OpenAI APIs."""

import json
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field


class TokenRecord(BaseModel):
    """Token usage metrics captured from an individual API call."""
    model: str = ""
    provider: str = "unknown"
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
        return TokenRecord(model=model, provider="anthropic", provider_reported=False)

    return TokenRecord(
        model=model,
        provider="anthropic",
        input_tokens=usage.get("input_tokens", 0),
        output_tokens=usage.get("output_tokens", 0),
        cache_read_tokens=usage.get("cache_read_input_tokens", 0),
        cache_write_tokens=usage.get("cache_creation_input_tokens", 0),
        provider_reported=True,
    )


def parse_openai_json_usage(data: Dict[str, Any]) -> TokenRecord:
    """Extract usage from standard OpenAI chat completions response JSON."""
    model = data.get("model", "")
    usage = data.get("usage", {})

    if not usage:
        return TokenRecord(model=model, provider="openai", provider_reported=False)

    cached_tokens = 0
    details = usage.get("prompt_tokens_details") or {}
    if isinstance(details, dict):
        cached_tokens = details.get("cached_tokens", 0)

    return TokenRecord(
        model=model,
        provider="openai",
        input_tokens=usage.get("prompt_tokens", 0),
        output_tokens=usage.get("completion_tokens", 0),
        cache_read_tokens=cached_tokens,
        cache_write_tokens=0,
        provider_reported=True,
    )


def parse_anthropic_sse_event(event_line: str, data_line: str) -> Dict[str, Any]:
    """Parse an Anthropic SSE event and return any usage delta discovered."""
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

    if data.get("type") == "message_start":
        msg = data.get("message", {})
        parsed["model"] = msg.get("model", "")
        usage = msg.get("usage", {})
        parsed["input_tokens"] = usage.get("input_tokens", 0)
        parsed["cache_read_tokens"] = usage.get("cache_read_input_tokens", 0)
        parsed["cache_write_tokens"] = usage.get("cache_creation_input_tokens", 0)

    elif data.get("type") == "message_delta":
        usage = data.get("usage", {})
        if "output_tokens" in usage:
            parsed["output_tokens"] = usage.get("output_tokens", 0)

    return parsed


def parse_openai_sse_event(data_line: str) -> Dict[str, Any]:
    """Parse an OpenAI SSE chunk (data: {...}) and return any usage delta discovered."""
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

    if data.get("model"):
        parsed["model"] = data["model"]

    usage = data.get("usage")
    if usage:
        parsed["input_tokens"] = usage.get("prompt_tokens", 0)
        parsed["output_tokens"] = usage.get("completion_tokens", 0)
        details = usage.get("prompt_tokens_details") or {}
        if isinstance(details, dict):
            parsed["cache_read_tokens"] = details.get("cached_tokens", 0)

    return parsed
