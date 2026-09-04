"""Tests for network proxy parsing, SSE handling, and cost calculation."""

import pytest
from decimal import Decimal
from fastapi.testclient import TestClient
from harnessbench.telemetry.costs import PricingModel, calculate_api_cost, get_pricing_for_model
from harnessbench.telemetry.proxy import app
from harnessbench.telemetry.tokens import (
    TokenRecord,
    parse_anthropic_json_usage,
    parse_anthropic_sse_event,
)


def test_parse_anthropic_json():
    payload = {
        "model": "claude-3-5-sonnet-20241022",
        "usage": {
            "input_tokens": 1500,
            "output_tokens": 300,
            "cache_read_input_tokens": 1000,
            "cache_creation_input_tokens": 200,
        },
    }
    record = parse_anthropic_json_usage(payload)
    assert record.model == "claude-3-5-sonnet-20241022"
    assert record.input_tokens == 1500
    assert record.output_tokens == 300
    assert record.cache_read_tokens == 1000
    assert record.cache_write_tokens == 200
    assert record.provider_reported is True


def test_parse_anthropic_sse():
    start_line = 'data: {"type":"message_start","message":{"model":"claude-3-5-sonnet-20241022","usage":{"input_tokens":500,"cache_read_input_tokens":100,"cache_creation_input_tokens":50}}}'
    delta = parse_anthropic_sse_event("message_start", start_line)
    assert delta["model"] == "claude-3-5-sonnet-20241022"
    assert delta["input_tokens"] == 500
    assert delta["cache_read_tokens"] == 100
    assert delta["cache_write_tokens"] == 50

    delta_line = 'data: {"type":"message_delta","usage":{"output_tokens":85}}'
    delta2 = parse_anthropic_sse_event("message_delta", delta_line)
    assert delta2["output_tokens"] == 85


def test_cost_calculation():
    pricing = PricingModel(
        input_cost_per_million=Decimal("3.00"),
        output_cost_per_million=Decimal("15.00"),
        cache_read_cost_per_million=Decimal("0.30"),
        cache_write_cost_per_million=Decimal("3.75"),
    )
    cost = pricing.calculate_cost(
        input_tokens=1_000_000,
        output_tokens=1_000_000,
        cache_read_tokens=1_000_000,
        cache_write_tokens=1_000_000,
    )
    # 3.00 + 15.00 + 0.30 + 3.75 = 22.05
    assert cost == 22.05

    sonnet_cost = calculate_api_cost("claude-3-5-sonnet-20241022", input_tokens=1000, output_tokens=500)
    assert sonnet_cost > 0.0


def test_proxy_session_endpoints():
    client = TestClient(app)

    # Start session
    resp = client.post(
        "/proxy/session/start",
        json={"run_id": "test_run_123", "task_id": "task_1", "harness": "aider", "model": "sonnet"},
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "session_started"

    # Summary
    resp_sum = client.get("/proxy/session/summary")
    assert resp_sum.status_code == 200
    assert resp_sum.json()["run_id"] == "test_run_123"

    # Stop session
    resp_stop = client.post("/proxy/session/stop")
    assert resp_stop.status_code == 200
    assert resp_stop.json()["status"] == "session_stopped"
