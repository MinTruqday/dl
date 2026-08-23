from typing import Literal
from pydantic import BaseModel, Field


class TaskEvaluation(BaseModel):
    status: Literal["PASS", "FAIL"] = Field(
        description="<critical_instructions>MUST be exactly 'PASS' if the agent's output is flawlessly coherent, usable, and safe. MUST be 'FAIL' if it contains ANY errors, hallucinations, violations of system rules, or is clearly suboptimal.</critical_instructions>"
    )
    feedback: str = Field(
        description="<metis_behavior>Brutally objective, highly specific actionable feedback explaining the PASS/FAIL verdict. If FAIL, pinpoint the exact logical flaw or line number. Do not use polite conversational filler. MUST NOT be empty.</metis_behavior>"
    )
    revised_task: str = Field(
        default="",
        description="<conditional_output>If status is 'FAIL', provide a meticulously revised, corrected version of the task instruction to strictly guide the next retry. Leave completely empty if status is 'PASS'.</conditional_output>",
    )


class DocumentGrade(BaseModel):
    is_relevant: bool = Field(
        description="<critical_instructions>Set to True ONLY if the document explicitly and directly contains factual information that resolves the user's query. Set to False if it is only tangentially related or lacks concrete answers.</critical_instructions>"
    )


class QualityEvaluation(BaseModel):
    relevance: float = Field(
        ge=0.0,
        le=1.0,
        description="<constraints>Score from 0.0 to 1.0 for how directly the response addresses the query.</constraints>",
    )
    grounding: float = Field(
        ge=0.0,
        le=1.0,
        description="<constraints>Score from 0.0 to 1.0 for how fully the response is supported by the supplied context.</constraints>",
    )
    completeness: float = Field(
        ge=0.0,
        le=1.0,
        description="<constraints>Score from 0.0 to 1.0 for coverage of every material part of the query.</constraints>",
    )
    overall: float = Field(
        ge=0.0,
        le=1.0,
        description="<constraints>Calibrated overall quality score from 0.0 to 1.0.</constraints>",
    )
    should_retry: bool = Field(
        description="<critical_instructions>Set to True when the response is unsafe, ungrounded, incomplete, or has an overall score below 0.6.</critical_instructions>"
    )
    feedback: str = Field(
        description="<output_format>Specific, actionable feedback pointing out exactly which part of the response is flawed and outlining the explicit logical steps required to fix it.</output_format>"
    )


class ErrorMessageJudgment(BaseModel):
    is_error_message: bool = Field(
        description="<critical_instructions>Set to True if the text contains a raw stack trace, HTTP error code, unhandled exception, Python/JS traceback, or a system failure message. Set to False if it is a natural language response (even if it politely apologizes).</critical_instructions>"
    )
    reason: str = Field(
        description="<critical_instructions>A specific, 1-2 sentence explanation of why this was classified as an error message or a valid output.</critical_instructions>"
    )


class HallucinationJudgment(BaseModel):
    is_hallucination_or_refusal: bool = Field(
        description="Set to True if the response refuses the prompt, states 'I do not know', uses AI-identity disclaimers, or contains hallucinated unverified facts."
    )
    confidence: float = Field(
        ge=0.0,
        le=1.0,
        description="<critical_instructions>Confidence score between 0.0 and 1.0 representing how certain you are of this judgment.</critical_instructions>",
    )
    explanation: str = Field(
        description="<critical_instructions>Detailed explanation of the exact claims that are hallucinated or why the refusal was detected.</critical_instructions>"
    )


class RelevanceJudgment(BaseModel):
    is_relevant: bool = Field(
        description="<critical_instructions>Set to True if the response directly addresses the core intent of the user's query without unnecessary pivoting.</critical_instructions>"
    )
    relevance_score: float = Field(
        ge=0.0,
        le=1.0,
        description="<critical_instructions>A continuous score from 0.0 to 1.0. Use 1.0 for perfect answers, 0.5 for partial answers, and 0.0 for completely unrelated garbage.</critical_instructions>",
    )
    feedback: str = Field(
        description="<critical_instructions>Actionable critique on what information is missing, hallucinatory, or well-executed regarding relevance.</critical_instructions>"
    )


class HallucinationGrade(BaseModel):
    is_refusal_or_hallucination: bool = Field(
        description="<critical_instructions>Set to True if the response refuses the prompt, states ignorance, or uses artificial identity markers. Set to False if it is a normal, helpful response.</critical_instructions>"
    )
    reason: str = Field(
        description="<critical_instructions>A concise 1-sentence reason explaining why the response was graded as a refusal/hallucination or a valid response.</critical_instructions>"
    )


class JudgeScores(BaseModel):
    accuracy: int = Field(
        ge=0,
        le=10,
        description="<output_format>Factual accuracy score from zero to ten.</output_format>",
    )
    completeness: int = Field(
        ge=0, le=10, description="<output_format>Coverage score from zero to ten.</output_format>"
    )
    relevance: int = Field(
        ge=0,
        le=10,
        description="<output_format>Task relevance score from zero to ten.</output_format>",
    )
    explanation: str = Field(
        min_length=1,
        max_length=2000,
        description="<output_format>Concise evidence for the scores.</output_format>",
    )
