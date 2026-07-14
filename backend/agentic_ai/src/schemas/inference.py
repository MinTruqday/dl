from typing import Any, List, Optional

from pydantic import BaseModel, Field

class GenerationRequest(BaseModel):
    prompt: str = Field(description="<input_context>The exact user request to be processed by Metis.</input_context>")
    max_tokens: int = Field(default=500, description="<constraints>Maximum token limit. Metis must enforce this strictly to prevent overflow.</constraints>")
    temperature: float = Field(default=0.3, description="<constraints>Temperature controls randomness. Keep low (0.0-0.3) for logic, higher (0.7) for creativity.</constraints>")

class TranslationRequest(BaseModel):
    text: str = Field(description="<input_context>The source text requiring translation.</input_context>")
    target_lang: str = Field(description="<constraints>The target ISO language code. Metis must translate with native fluency.</constraints>")

class CodeRequest(BaseModel):
    prompt: str = Field(description="<input_context>The coding task specification.</input_context>")
    language: str = Field(default="python", description="<constraints>The target programming language. Must follow idiomatic standards.</constraints>")

class GrammarRequest(BaseModel):
    text: str

class SummarizeRequest(BaseModel):
    text: str
    language: str = "auto"

class ActionRequest(BaseModel):
    action: str
    text: str
    context: Optional[str] = ""

class CitationRequest(BaseModel):
    text: str
    style: str = "APA"

class ToneRequest(BaseModel):
    text: str
    tone: str
    expansion: bool = False

class ReviewRequest(BaseModel):
    text: str
    criteria: Optional[List[str]] = None

class SynthesisRequest(BaseModel):
    document_ids: List[str]
    query: str

class PlagiarismCheckRequest(BaseModel):
    content: str

class CoverGenerateRequest(BaseModel):
    style: str = "minimalist"

class AISuggestionRequest(BaseModel):
    context: str

class GlossaryRequest(BaseModel):
    text: str

class StyleImitationRequest(BaseModel):
    text: str
    style_sample: str
    target_length: Optional[int] = None

class DraftWithMemoryRequest(BaseModel):
    prompt: str

class ExtractToStorageRequest(BaseModel):
    text: str
    extraction_goals: List[str]

class WebFactCheckRequest(BaseModel):
    text: str

class ComplianceScreenRequest(BaseModel):
    text: str

class SemanticDiffRequest(BaseModel):
    text1: str
    text2: str

class MemoryUserEditsRequest(BaseModel):
    action: str
    content: str
    memory_id: Optional[str] = None
