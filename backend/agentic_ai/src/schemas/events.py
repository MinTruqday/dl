from typing import Any, Dict, Optional
from pydantic import BaseModel, Field

class WebhookPayload(BaseModel):
    """
    Standardizes external incoming webhook payloads.
    Constraint: Must blindly accept arbitrary dictionaries in the payload field for processing by downstream event handlers.
    """
    event_type: str = Field(default="webhook", description="<input_context>The type of the incoming event.</input_context>")
    source: str = Field(default="external", description="<input_context>The origin of the event.</input_context>")
    payload: Dict[str, Any] = Field(default_factory=dict, description="<critical_instructions>The actual payload dictionary.</critical_instructions>")

class CreateScheduleRequest(BaseModel):
    """
    Registers a recurring background task.
    Constraint: interval_seconds MUST be strictly enforced by the event loop to prevent flooding.
    """
    name: str = Field(description="<input_context>Name of the scheduled task.</input_context>")
    interval_seconds: int = Field(description="<critical_instructions>Interval in seconds between runs.</critical_instructions>")
    event_type: str = Field(default="system_heartbeat", description="<input_context>Type of the recurring event.</input_context>")
    payload_template: Dict[str, Any] = Field(default_factory=dict, description="<input_context>Template for the payload.</input_context>")
    enabled: bool = Field(default=True, description="<conditional_output>Whether the task is currently active.</conditional_output>")

class ScheduleResponse(BaseModel):
    schedule_id: str = Field(description="<input_context>Unique identifier for the schedule.</input_context>")
    name: str = Field(description="<input_context>Name of the scheduled task.</input_context>")
    interval_seconds: int = Field(description="<critical_instructions>Interval in seconds between runs.</critical_instructions>")
    event_type: str = Field(description="<input_context>Type of the recurring event.</input_context>")
    enabled: bool = Field(description="<conditional_output>Whether the task is active.</conditional_output>")
    run_count: int = Field(description="<input_context>Total number of times the task has run.</input_context>")
    last_run_at: Optional[str] = Field(default=None, description="<input_context>Timestamp of the last execution.</input_context>")
