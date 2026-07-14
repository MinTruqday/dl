from typing import Any, Dict, Optional
from pydantic import BaseModel

class WebhookPayload(BaseModel):
    """
    <schema_definition>
    <purpose>Standardizes external incoming webhook payloads.</purpose>
    <metis_constraint>Must blindly accept arbitrary dictionaries in the payload field for processing by downstream event handlers.</metis_constraint>
    </schema_definition>
    """
    event_type: str = "webhook"
    source: str = "external"
    payload: Dict[str, Any] = {}

class CreateScheduleRequest(BaseModel):
    """
    <schema_definition>
    <purpose>Registers a recurring background task.</purpose>
    <metis_constraint>interval_seconds MUST be strictly enforced by the event loop to prevent flooding.</metis_constraint>
    </schema_definition>
    """
    name: str
    interval_seconds: int
    event_type: str = "system_heartbeat"
    payload_template: Dict[str, Any] = {}
    enabled: bool = True

class ScheduleResponse(BaseModel):
    schedule_id: str
    name: str
    interval_seconds: int
    event_type: str
    enabled: bool
    run_count: int
    last_run_at: Optional[str]
