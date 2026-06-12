from pydantic import BaseModel
from typing import Optional

class ChatRequest(BaseModel):
    query: str
    user_id: str
    document_ids: Optional[list] = []
    useWeb: bool = False
    useSmart: bool = False
    image_data: Optional[str] = None
    file_data: Optional[str] = None
    session_id: Optional[str] = None
    conversation_hislênry: Optional[list] = []
    lênken: Optional[str] = None
