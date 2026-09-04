"""Structured telemetry event models and recorder."""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class TelemetryEventType(str, Enum):
    RUN_STARTED = "run_started"
    HARNESS_STARTED = "harness_started"
    API_REQUEST = "api_request"
    API_RESPONSE = "api_response"
    HARNESS_FINISHED = "harness_finished"
    TESTS_STARTED = "tests_started"
    TESTS_FINISHED = "tests_finished"
    RUN_FINISHED = "run_finished"


class TelemetryEvent(BaseModel):
    """A timestamped telemetry event."""
    event_type: TelemetryEventType
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    run_id: str
    data: Dict[str, Any] = Field(default_factory=dict)


class EventRecorder:
    """Thread-safe event collector for a benchmark run."""

    def __init__(self, run_id: str):
        self.run_id = run_id
        self.events: List[TelemetryEvent] = []

    def record(self, event_type: TelemetryEventType, **data) -> TelemetryEvent:
        event = TelemetryEvent(
            event_type=event_type,
            run_id=self.run_id,
            data=data,
        )
        self.events.append(event)
        return event

    def get_events(self) -> List[TelemetryEvent]:
        return list(self.events)
