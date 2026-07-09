from typing import Any, Dict, Optional
from pydantic import BaseModel

class WebhookPayload(BaseModel):
    event_type: str = "webhook"
    source: str = "external"
    payload: Dict[str, Any] = {}

class CreateScheduleRequest(BaseModel):
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
