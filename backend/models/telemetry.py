from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List, Dict
from bson import ObjectId

class TelemetryEvent(BaseModel):
    event_type: str = Field(..., description="E.g., ping, scroll, idle, active, exit")
    client_fps: Optional[float] = None
    scroll_speed: Optional[float] = None
    progress_percentage: Optional[float] = None
    viewport_width: Optional[int] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class ReadingSession(BaseModel):
    id: str = Field(default_factory=lambda: str(ObjectId()), alias="_id")
    document_id: str
    chapter_index: int
    user_id: Optional[str] = None
    device_fingerprint: str
    start_time: datetime = Field(default_factory=datetime.utcnow)
    end_time: Optional[datetime] = None
    total_active_seconds: float = 0.0
    total_idle_seconds: float = 0.0
    highest_scroll_speed: float = 0.0
    max_progress: float = 0.0
    events: List[TelemetryEvent] = []
    
    class Config:
        populate_by_name = True
