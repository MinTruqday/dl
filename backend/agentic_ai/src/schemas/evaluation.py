from typing import Literal
from pydantic import BaseModel, Field

class TaskEvaluation(BaseModel):
    status: Literal["PASS", "FAIL"] = Field(
        description="CRITICAL: MUST be exactly 'PASS' if the agent's output is coherent and usable, or 'FAIL' if it contains errors, hallucinations, or is clearly wrong."
    )
    feedback: str = Field(
        description="Specific, actionable feedback explaining the reason for the PASS or FAIL verdict. Cite the exact problem or confirm the quality. CRITICAL: MUST NOT be empty."
    )
    revised_task: str = Field(
        default="",
        description="If status is 'FAIL', provide a revised, corrected version of the task instruction to guide the next retry. Leave empty if status is 'PASS'."
    )

class DocumentGrade(BaseModel):
    is_relevant: bool = Field(description="CRITICAL: Set to True ONLY if the document explicitly contains information that directly helps answer the user's query. Otherwise, False.")

class QualityEvaluation(BaseModel):
    is_hallucination: bool = Field(
        description="CRITICAL: Set to True if the response contains unverified claims, fabricated facts, or information directly contradicting the retrieved context."
    )
    feedback: str = Field(description="Specific, actionable feedback pointing out exactly which part of the response is flawed and how to fix it.")
