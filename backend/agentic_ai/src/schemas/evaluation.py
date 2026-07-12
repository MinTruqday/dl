from typing import Literal
from pydantic import BaseModel, Field

class TaskEvaluation(BaseModel):
    status: Literal["PASS", "FAIL"] = Field()
    feedback: str = Field()
    revised_task: str = Field(default="")

class DocumentGrade(BaseModel):
    is_relevant: bool = Field(description="CRITICAL: Set to True ONLY if the document explicitly contains information that directly helps answer the user's query. Otherwise, False.")

class QualityEvaluation(BaseModel):
    is_hallucination: bool = Field(
        description="CRITICAL: Set to True if the response contains unverified claims, fabricated facts, or information directly contradicting the retrieved context."
    )
    feedback: str = Field(description="Specific, actionable feedback pointing out exactly which part of the response is flawed and how to fix it.")
