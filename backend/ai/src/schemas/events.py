import json
from typing import Any, Dict, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


class EventRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    @field_validator("payload", "payload_template", check_fields=False)
    @classmethod
    def validate_payload_size(cls, value):
        if len(json.dumps(value, ensure_ascii=False, default=str).encode()) > 65536:
            raise ValueError("Event payload exceeds 64 KiB")
        return value


class WebhookPayload(EventRequest):
    """
    Standardizes authenticated internal webhook payloads
    Rejects unknown event types oversized payloads and extra fields
    """
    event_type: Literal[
        "webhook",
        "document_uploaded",
        "user_query",
        "system_heartbeat",
        "document_deleted",
        "user_registered",
    ] = Field(default="webhook", description="<input_context>The type of the incoming event.</input_context>")
    source: str = Field(default="external", min_length=1, max_length=100, pattern=r"^[a-zA-Z0-9_.:-]+$", description="<input_context>The origin of the event.</input_context>")
    payload: Dict[str, Any] = Field(default_factory=dict, description="<critical_instructions>The actual payload dictionary.</critical_instructions>")


class CreateScheduleRequest(EventRequest):
    """
    Registers a recurring background task.
    Constraint: interval_seconds MUST be strictly enforced by the event loop to prevent flooding.
    """
    name: str = Field(min_length=1, max_length=100, description="<input_context>Name of the scheduled task.</input_context>")
    interval_seconds: int = Field(ge=60, le=2592000, description="<critical_instructions>Interval in seconds between runs.</critical_instructions>")
    event_type: Literal[
        "system_heartbeat",
        "document_uploaded",
        "user_query",
        "webhook",
    ] = Field(default="system_heartbeat", description="<input_context>Type of the recurring event.</input_context>")
    payload_template: Dict[str, Any] = Field(default_factory=dict, description="<input_context>Template for the payload.</input_context>")
    enabled: bool = Field(default=True, description="<conditional_output>Whether the task is currently active.</conditional_output>")


class ManualTriggerRequest(EventRequest):
    payload: Dict[str, Any] = Field(default_factory=dict, description="<input_context>Bounded payload passed to the selected event handler.</input_context>")


class ScheduleResponse(EventRequest):
    schedule_id: str = Field(description="<input_context>Unique identifier for the schedule.</input_context>")
    name: str = Field(description="<input_context>Name of the scheduled task.</input_context>")
    interval_seconds: int = Field(description="<critical_instructions>Interval in seconds between runs.</critical_instructions>")
    event_type: str = Field(description="<input_context>Type of the recurring event.</input_context>")
    enabled: bool = Field(description="<conditional_output>Whether the task is active.</conditional_output>")
    run_count: int = Field(description="<input_context>Total number of times the task has run.</input_context>")
    last_run_at: Optional[str] = Field(default=None, description="<input_context>Timestamp of the last execution.</input_context>")
