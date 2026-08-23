from typing import Literal, Optional

from pydantic import BaseModel, Field


class InterventionFeedbackRequest(BaseModel):
    status: Literal["APPROVED", "REJECTED", "CORRECTED"] = Field(
        description="<critical_instructions>Resolution selected by the authenticated owner</critical_instructions>"
    )
    human_feedback: Optional[str] = Field(
        default=None,
        max_length=4000,
        description="<input_context>Optional explanation supplied by the authenticated owner</input_context>",
    )
    correction: Optional[str] = Field(
        default=None,
        max_length=10000,
        description="<input_context>Optional corrected action supplied by the authenticated owner</input_context>",
    )
    scope: Literal["once", "session", "safe_session"] = Field(
        default="once",
        description="How long this approval applies within the current conversation",
    )
