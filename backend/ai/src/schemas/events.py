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
    event_type: Literal[
        "webhook",
        "document_uploaded",
        "user_query",
        "system_heartbeat",
        "document_deleted",
        "user_registered",
    ] = Field(
        default="webhook",
        description="Incoming event type",
    )
    source: str = Field(
        default="external",
        min_length=1,
        max_length=100,
        pattern=r"^[a-zA-Z0-9_.:-]+$",
        description="Event source",
    )
    payload: Dict[str, Any] = Field(
        default_factory=dict,
        description="Event payload",
    )


class CreateScheduleRequest(EventRequest):
    name: str = Field(
        min_length=1,
        max_length=100,
        description="Schedule name",
    )
    interval_seconds: int = Field(
        ge=60,
        le=2592000,
        description="Interval between runs in seconds",
    )
    event_type: Literal["system_heartbeat", "document_uploaded", "user_query", "webhook"] = Field(
        default="system_heartbeat",
        description="Scheduled event type",
    )
    payload_template: Dict[str, Any] = Field(
        default_factory=dict, description="Event payload template"
    )
    enabled: bool = Field(
        default=True,
        description="Whether the schedule is enabled",
    )


class ManualTriggerRequest(EventRequest):
    payload: Dict[str, Any] = Field(
        default_factory=dict,
        description="Bounded payload passed to the event handler",
    )


class ScheduleResponse(EventRequest):
    schedule_id: str = Field(
        description="Schedule identifier"
    )
    name: str = Field(description="Schedule name")
    interval_seconds: int = Field(
        description="Interval between runs in seconds"
    )
    event_type: str = Field(
        description="Scheduled event type"
    )
    enabled: bool = Field(
        description="Whether the schedule is enabled"
    )
    run_count: int = Field(
        description="Total schedule run count"
    )
    last_run_at: Optional[str] = Field(
        default=None, description="Most recent run time"
    )
