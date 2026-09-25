from typing import Literal

from pydantic import BaseModel, Field


class TaskEvaluation(BaseModel):
    status: Literal["PASS", "FAIL"] = Field(
        description="PASS when the result is accurate complete grounded and safe otherwise FAIL"
    )
    feedback: str = Field(
        description="Specific evidence grounded evaluation feedback"
    )
    revised_task: str = Field(
        default="",
        description="Revised task when status is FAIL and empty when status is PASS",
    )


class DocumentGrade(BaseModel):
    is_relevant: bool = Field(
        description="True when the document directly contains information that addresses the query"
    )


class QualityEvaluation(BaseModel):
    relevance: float = Field(
        ge=0.0,
        le=1.0,
        description="Degree to which the result directly answers the query from zero to one",
    )
    grounding: float = Field(
        ge=0.0,
        le=1.0,
        description="Degree of support from the supplied context from zero to one",
    )
    completeness: float = Field(
        ge=0.0,
        le=1.0,
        description="Coverage of material query elements from zero to one",
    )
    overall: float = Field(
        ge=0.0,
        le=1.0,
        description="Overall quality score from zero to one",
    )
    should_retry: bool = Field(
        description="True when the result is unsafe ungrounded incomplete or below the quality threshold"
    )
    feedback: str = Field(
        description="Specific feedback about deficiencies and how to correct them"
    )


class ErrorMessageJudgment(BaseModel):
    is_error_message: bool = Field(
        description="True when the text is a raw system or technical error"
    )
    reason: str = Field(
        description="Concise reason for the classification"
    )


class HallucinationJudgment(BaseModel):
    is_hallucination_or_refusal: bool = Field(
        description="True when the result refuses or contains unverified information"
    )
    confidence: float = Field(
        ge=0.0,
        le=1.0,
        description="Judgment confidence from zero to one",
    )
    explanation: str = Field(
        description="Specific explanation of the unsupported claim or detected refusal"
    )


class RelevanceJudgment(BaseModel):
    is_relevant: bool = Field(
        description="True when the result directly addresses the primary query intent"
    )
    relevance_score: float = Field(
        ge=0.0,
        le=1.0,
        description="Relevance score from zero to one",
    )
    feedback: str = Field(
        description="Feedback about missing unsupported or relevant content"
    )


class HallucinationGrade(BaseModel):
    is_refusal_or_hallucination: bool = Field(
        description="True when the result refuses or contains unverified information"
    )
    reason: str = Field(
        description="Concise reason for the judgment"
    )


class JudgeScores(BaseModel):
    accuracy: int = Field(
        ge=0,
        le=10,
        description="Accuracy score from zero to ten",
    )
    completeness: int = Field(
        ge=0, le=10, description="Completeness score from zero to ten"
    )
    relevance: int = Field(
        ge=0,
        le=10,
        description="Relevance score from zero to ten",
    )
    explanation: str = Field(
        min_length=1,
        max_length=2000,
        description="Concise evidence for the assigned scores",
    )
