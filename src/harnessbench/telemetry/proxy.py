"""FastAPI & httpx network interception proxy for ground-truth API telemetry."""

import asyncio
import json
import os
import threading
import time
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Any, AsyncIterator, Dict, List, Optional

import httpx
import uvicorn
from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse, StreamingResponse

from harnessbench.telemetry.costs import calculate_api_cost
from harnessbench.telemetry.tokens import (
    ApiUsageSummary,
    TokenRecord,
    parse_anthropic_json_usage,
    parse_anthropic_sse_event,
)

DEFAULT_UPSTREAM_ANTHROPIC = "https://api.anthropic.com"


class ProxySession:
    """Active telemetry capture session."""

    def __init__(self, run_id: str = "default", task_id: str = "", harness: str = "", model: str = ""):
        self.run_id = run_id
        self.task_id = task_id
        self.harness = harness
        self.model = model
        self.is_active = True
        self.records: List[TokenRecord] = []
        self.summary = ApiUsageSummary()

    def add_record(self, record: TokenRecord) -> None:
        if not record.model and self.model:
            record.model = self.model
        self.records.append(record)
        self.summary.add(record)

    def get_cost_usd(self) -> float:
        total_cost = 0.0
        for r in self.records:
            total_cost += calculate_api_cost(
                model=r.model or self.model or "default",
                input_tokens=r.input_tokens,
                output_tokens=r.output_tokens,
                cache_read_tokens=r.cache_read_tokens,
                cache_write_tokens=r.cache_write_tokens,
            )
        return float(round(total_cost, 6))


# Global proxy state
_active_session: Optional[ProxySession] = None
_session_lock = threading.Lock()
_upstream_base_url = os.environ.get("HARNESSBENCH_UPSTREAM_URL", DEFAULT_UPSTREAM_ANTHROPIC)


def get_current_session() -> Optional[ProxySession]:
    with _session_lock:
        return _active_session


def set_current_session(session: Optional[ProxySession]) -> None:
    global _active_session
    with _session_lock:
        _active_session = session


def set_upstream_base_url(url: str) -> None:
    global _upstream_base_url
    _upstream_base_url = url.rstrip("/")


app = FastAPI(title="HarnessBench Network Interceptor Proxy")


@app.post("/proxy/session/start")
async def start_session(payload: Dict[str, Any]):
    session = ProxySession(
        run_id=payload.get("run_id", "manual"),
        task_id=payload.get("task_id", ""),
        harness=payload.get("harness", ""),
        model=payload.get("model", ""),
    )
    set_current_session(session)
    return {"status": "session_started", "run_id": session.run_id}


@app.post("/proxy/session/stop")
async def stop_session():
    session = get_current_session()
    if not session:
        return {"status": "no_active_session"}
    session.is_active = False
    return {
        "status": "session_stopped",
        "run_id": session.run_id,
        "total_requests": session.summary.total_requests,
        "input_tokens": session.summary.input_tokens,
        "output_tokens": session.summary.output_tokens,
        "cache_read_tokens": session.summary.cache_read_tokens,
        "total_tokens": session.summary.total_tokens,
        "cost_usd": session.get_cost_usd(),
    }


@app.get("/proxy/session/summary")
async def get_session_summary():
    session = get_current_session()
    if not session:
        return {"status": "no_active_session", "total_requests": 0}
    return {
        "run_id": session.run_id,
        "is_active": session.is_active,
        "total_requests": session.summary.total_requests,
        "input_tokens": session.summary.input_tokens,
        "output_tokens": session.summary.output_tokens,
        "cache_read_tokens": session.summary.cache_read_tokens,
        "total_tokens": session.summary.total_tokens,
        "cost_usd": session.get_cost_usd(),
    }


# Forwarding & Interception route
@app.api_route("/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH", "HEAD", "OPTIONS"])
async def intercept_traffic(request: Request, path: str):
    # Ignore proxy internal control endpoints
    if path.startswith("proxy/"):
        return JSONResponse(status_code=404, content={"detail": "Not found"})

    target_url = f"{_upstream_base_url}/{path}"
    headers = dict(request.headers)
    headers.pop("host", None)
    headers.pop("content-length", None)

    body = await request.body()
    req_json: Dict[str, Any] = {}
    requested_model = ""
    try:
        if body:
            req_json = json.loads(body.decode("utf-8"))
            requested_model = req_json.get("model", "")
    except Exception:
        pass

    start_time = time.perf_counter()

    # Make upstream request
    client = httpx.AsyncClient(timeout=120.0)
    try:
        req = client.build_request(
            method=request.method,
            url=target_url,
            headers=headers,
            params=request.query_params,
            content=body,
        )
        upstream_resp = await client.send(req, stream=True)
    except Exception as e:
        await client.aclose()
        return JSONResponse(status_code=502, content={"error": f"Upstream proxy failed: {str(e)}"})

    content_type = upstream_resp.headers.get("content-type", "")

    # Handle streaming SSE responses
    if "text/event-stream" in content_type:
        async def stream_generator() -> AsyncIterator[bytes]:
            current_model = requested_model
            input_tokens = 0
            output_tokens = 0
            cache_read_tokens = 0
            cache_write_tokens = 0
            current_event = ""

            try:
                async for line in upstream_resp.aiter_lines():
                    yield (line + "\n").encode("utf-8")

                    line_str = line.strip()
                    if line_str.startswith("event:"):
                        current_event = line_str[len("event:"):].strip()
                    elif line_str.startswith("data:"):
                        delta = parse_anthropic_sse_event(current_event, line_str)
                        if delta:
                            if delta.get("model"):
                                current_model = delta["model"]
                            input_tokens += delta.get("input_tokens", 0)
                            output_tokens += delta.get("output_tokens", 0)
                            cache_read_tokens += delta.get("cache_read_tokens", 0)
                            cache_write_tokens += delta.get("cache_write_tokens", 0)
            finally:
                await upstream_resp.aclose()
                await client.aclose()
                latency = time.perf_counter() - start_time
                session = get_current_session()
                if session and session.is_active:
                    record = TokenRecord(
                        model=current_model or requested_model,
                        input_tokens=input_tokens,
                        output_tokens=output_tokens,
                        cache_read_tokens=cache_read_tokens,
                        cache_write_tokens=cache_write_tokens,
                        provider_reported=(input_tokens > 0 or output_tokens > 0),
                        status_code=upstream_resp.status_code,
                        latency_seconds=latency,
                    )
                    session.add_record(record)

        resp_headers = dict(upstream_resp.headers)
        resp_headers.pop("content-length", None)
        return StreamingResponse(
            stream_generator(),
            status_code=upstream_resp.status_code,
            headers=resp_headers,
            media_type="text/event-stream",
        )

    # Handle standard non-streaming responses
    try:
        content = await upstream_resp.aread()
    finally:
        await upstream_resp.aclose()
        await client.aclose()

    latency = time.perf_counter() - start_time

    # Attempt to parse provider token usage
    try:
        resp_json = json.loads(content.decode("utf-8"))
        record = parse_anthropic_json_usage(resp_json)
        if not record.model and requested_model:
            record.model = requested_model
        record.status_code = upstream_resp.status_code
        record.latency_seconds = latency

        session = get_current_session()
        if session and session.is_active:
            session.add_record(record)
    except Exception:
        pass

    resp_headers = dict(upstream_resp.headers)
    resp_headers.pop("content-length", None)
    return Response(
        content=content,
        status_code=upstream_resp.status_code,
        headers=resp_headers,
        media_type=content_type or "application/json",
    )


class ProxyServer:
    """Manages the lifecycle of a local uvicorn proxy server in a background thread."""

    def __init__(self, host: str = "127.0.0.1", port: int = 8088, upstream_url: Optional[str] = None):
        self.host = host
        self.port = port
        self.upstream_url = upstream_url or DEFAULT_UPSTREAM_ANTHROPIC
        self.server: Optional[uvicorn.Server] = None
        self.thread: Optional[threading.Thread] = None

    @property
    def base_url(self) -> str:
        return f"http://{self.host}:{self.port}"

    def start(self) -> None:
        set_upstream_base_url(self.upstream_url)
        config = uvicorn.Config(app=app, host=self.host, port=self.port, log_level="warning")
        self.server = uvicorn.Server(config)

        self.thread = threading.Thread(target=self.server.run, daemon=True)
        self.thread.start()

        # Wait briefly for proxy to bind
        time.sleep(0.5)

    def stop(self) -> None:
        if self.server:
            self.server.should_exit = True
            if self.thread and self.thread.is_alive():
                self.thread.join(timeout=2.0)
            self.server = None
            self.thread = None

    def __enter__(self) -> "ProxyServer":
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.stop()
