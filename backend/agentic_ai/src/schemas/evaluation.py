from typing import Literal
from pydantic import BaseModel, Field

class TaskEvaluation(BaseModel):
    status: Literal["PASS", "FAIL"] = Field(
        ...,
        description="<critical_instructions>MUST be exactly 'PASS' if the agent's output is flawlessly coherent, usable, and safe. MUST be 'FAIL' if it contains ANY errors, hallucinations, violations of system rules, or is clearly suboptimal.</critical_instructions>"
    )
    feedback: str = Field(
        ...,
        description="<metis_behavior>Brutally objective, highly specific actionable feedback explaining the PASS/FAIL verdict. If FAIL, pinpoint the exact logical flaw or line number. Do not use polite conversational filler. MUST NOT be empty.</metis_behavior>"
    )
    revised_task: str = Field(
        default="",
        description="<conditional_output>If status is 'FAIL', provide a meticulously revised, corrected version of the task instruction to strictly guide the next retry. Leave completely empty if status is 'PASS'.</conditional_output>"
    )

class DocumentGrade(BaseModel):
    is_relevant: bool = Field(
        ...,
        description="<critical_instructions>Set to True ONLY if the document explicitly and directly contains factual information that resolves the user's query. Set to False if it is only tangentially related or lacks concrete answers.</critical_instructions>"
    )

class QualityEvaluation(BaseModel):
    is_hallucination: bool = Field(
        ...,
        description="<critical_instructions>Set to True if the response contains ANY unverified claims, fabricated facts, hallucinated APIs, or information directly contradicting the retrieved context.</critical_instructions>"
    )
    feedback: str = Field(
        ...,
        description="<output_format>Specific, actionable feedback pointing out exactly which part of the response is flawed and outlining the explicit logical steps required to fix it.</output_format>"
    )
