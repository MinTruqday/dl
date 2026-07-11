from typing import List, Optional
from pydantic import BaseModel, Field

class PlanStep(BaseModel):
    agent: str = Field(description="The name of the execution agent")
    task: str = Field(description="Detailed task description")

class ExecutionPlan(BaseModel):
    reasoning: str = Field(description="Reasoning chain before breaking down steps")
    steps: List[PlanStep] = Field(description="List of execution steps")

class IngestRequest(BaseModel):
    document_id: str

class FeedbackRequest(BaseModel):
    session_id: str
    message_id: str
    user_id: str
    vote_type: str = Field(
        ..., description="Must choose like, dislike, or report an issue"
    )
    comment: Optional[str] = ""

from typing import Literal

class TaskEvaluation(BaseModel):
    status: Literal["PASS", "FAIL"] = Field()
    feedback: str = Field()
    revised_task: str = Field(default="")

class ContextQuery(BaseModel):
    question: str = Field(description="The rewritten question")

class GraphRoute(BaseModel):
    route: Literal["rag", "direct"] = Field(
        description="Route: 'rag' or 'direct'"
    )

class RetrievalStrategy(BaseModel):
    is_simple: bool = Field(
        description="True if simple question, False if sub-queries needed"
    )
    queries: List[str] = Field(description="List of optimal search queries")

class QueryOptimization(BaseModel):
    question: str = Field(description="The optimal search query")

class DocumentGrade(BaseModel):
    is_relevant: bool = Field(description="Whether the document is relevant to the question")

class RouteDecision(BaseModel):
    reasoning: str = Field(description="Step-by-step reasoning process")
    route: Literal["action", "knowledge", "chat"] = Field(
        description="Selected route: action, knowledge, or chat"
    )
    answer: str = Field(default="", description="Return empty string if not chat")

class QualityEvaluation(BaseModel):
    is_hallucination: bool = Field(
        description="Whether the response contains hallucinated or incorrect information"
    )
    feedback: str = Field(description="Feedback explaining the reasoning")

class MultiQueryOutput(BaseModel):
    queries: List[str] = Field(
        description="List of 3 rewritten queries"
    )

class SecurityEvaluation(BaseModel):
    is_malicious: bool = Field(description="True if the input contains prompt injections, jailbreaks, or malicious intents")
    has_pii: bool = Field(description="True if the input contains PII (Personally Identifiable Information)")
    has_credentials: bool = Field(description="True if the input contains credentials, API keys, or passwords")
    sanitized_text: str = Field(description="The input text with all PII and sensitive credentials redacted")
    reason: str = Field(description="Explanation of the detection result")

class FinetuneJobUpdate(BaseModel):
    progress: Optional[float] = None
    current_epoch: Optional[int] = None
    current_loss: Optional[float] = None
    status: Optional[str] = None
    adapter_path: Optional[str] = None
    merged_model_name: Optional[str] = None
    error_message: Optional[str] = None
    best_loss: Optional[float] = None
