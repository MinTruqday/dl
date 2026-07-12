from typing import Any, List, Optional

from pydantic import BaseModel

class GenerationRequest(BaseModel):
    prompt: str
    max_tokens: int = 500
    temperature: float = 0.3

class TranslationRequest(BaseModel):
    text: str
    target_lang: str

class CodeRequest(BaseModel):
    prompt: str
    language: str = "python"

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
    action: str  # add, update, delete
    content: str
    memory_id: Optional[str] = None
