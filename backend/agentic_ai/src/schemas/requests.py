from typing import List, Optional
from pydantic import BaseModel, Field


class CreateDocument(BaseModel):
    title: str = Field(description='The title of the document')
    description: str = Field(description='A short summary of the document')
    format: str = Field(description='Must be json for Editor block or latex for LaTeX format')
    content: str = Field(description='The main body of the document representation format correctly constructed')


class UpdateDocument(BaseModel):
    document_id: str = Field(description='The unique identifier of the document to update')
    new_content: str = Field(description='The new content for the document strictly matching format requirements')


class PlanStep(BaseModel):
    agent: str = Field(description='Name of the execution agent designated for this particular step')
    task: str = Field(description='Specific task description for the assigned agent to execute')


class ExecutionPlan(BaseModel):
    reasoning: str = Field(description='Chain of thought reasoning evaluated before decomposing the execution steps')
    steps: List[PlanStep] = Field(description='Ordered list of execution steps formulated to fulfill the request')


class IngestRequest(BaseModel):
    document_id: str


class FeedbackRequest(BaseModel):
    session_id: str
    message_id: str
    user_id: str
    vote_type: str = Field(..., description='Must be upvote downvote or hallucination assessment report')
    comment: Optional[str] = ''


class ChatRequest(BaseModel):
    query: str
    user_id: str
    document_ids: Optional[list] = []
    useWeb: bool = False
    useSmart: bool = False
    image_data: Optional[str] = None
    file_data: Optional[str] = None
    session_id: Optional[str] = None
    conversation_history: Optional[list] = []
    token: Optional[str] = None
    ai_tier: str = 'BASIC'
    role: str = 'reader'