from typing import Optional
from pydantic import BaseModel, Field

class FeedbackRequest(BaseModel):
    session_id: str = Field(min_length=1, max_length=128, description="<input_context>Conversation session containing the evaluated response.</input_context>")
    message_id: str = Field(min_length=1, max_length=128, description="<input_context>Assistant message receiving the feedback.</input_context>")
    user_id: str = Field(default="", max_length=128, description="<security_context>Ignored client identity field retained for compatibility because authenticated identity is authoritative.</security_context>")
    vote_type: str = Field(description="<critical_instructions>MUST be exactly one of: 'like', 'dislike', or 'report_issue'. Use this to categorize the user's feedback intent.</critical_instructions>")
    comment: Optional[str] = Field(default="", max_length=5000, description="<input_context>Optional user explanation for the selected feedback category.</input_context>")
