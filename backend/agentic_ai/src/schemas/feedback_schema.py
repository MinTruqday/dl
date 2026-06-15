from typing import Optional

from pydantic import BaseModel, Field


class FeedbackRequest(BaseModel):
    session_id: str
    message_id: str
    user_id: str
    vote_type: str = Field(
        ..., description="Must be upvote downvote or hallucination_report"
    )
    comment: Optional[str] = ""