from pydantic import BaseModel, Field

class ReviewerEvaluation(BaseModel):
    is_approved: bool = Field(..., description="<critical_instructions>True if code meets architectural standards.</critical_instructions>")
    feedback: str = Field(..., description="<critical_instructions>Detailed feedback or reasons for rejection.</critical_instructions>")
