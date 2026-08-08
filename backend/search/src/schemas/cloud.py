from typing import List, Optional
from pydantic import BaseModel

class CloudSearchFilter(BaseModel):
    query_text: Optional[str] = None
    mime_type: Optional[str] = None
    extension: Optional[str] = None
    min_size_mb: Optional[float] = None
    max_size_mb: Optional[float] = None

class PreviewPayload(BaseModel):
    item_id: str
    name: Optional[str] = None
    size: Optional[int] = None
    preview_type: str
    stream_url: Optional[str] = None
    can_preview: bool
