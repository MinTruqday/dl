from typing import Optional
from pydantic import BaseModel, Field

class FeedbackRequest(BaseModel):
    session_id: str
    message_id: str
    user_id: str
    vote_type: str = Field(
        ..., description="CRITICAL: MUST be exactly one of: 'like', 'dislike', or 'report_issue'. Use this to categorize the user's feedback intent."
    )
    comment: Optional[str] = ""
