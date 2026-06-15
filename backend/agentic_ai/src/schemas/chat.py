from typing import Optional
from pydantic import BaseModel

class ChatRequest(BaseModel):
    query: str
    user_id: str
    document_ids: Optional[list] = []
    useWeb: bool = False
    useSmart: bool = False
    image_data: Optional[str] = None
    file_data: Optional[str] = None
    session_id: Optional[str] = None
    conversation_history: Optional[list] = []
    token: Optional[str] = None
