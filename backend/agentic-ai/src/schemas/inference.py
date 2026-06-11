from pydantic import BaseModel
from typing import List, Optional, Any

class GenerationRequest(BaseModel):
    prompt: str
    max_tokens: int = 500
    temperature: float = 0.3

class TranslationRequest(BaseModel):
    text: str
    target_lang: str

class SentimentRequest(BaseModel):
    texts: Optional[List[str]] = None
    document_id: Optional[str] = None

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
