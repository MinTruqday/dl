from typing import Annotated, List, Optional

from pydantic import BaseModel, Field

class GenerationRequest(BaseModel):
    prompt: str = Field(min_length=1, max_length=100000, description="<input_context>The exact user request to be processed by Metis.</input_context>")
    max_tokens: int = Field(default=500, ge=1, le=4000, description="<constraints>Maximum token limit. Metis must enforce this strictly to prevent overflow.</constraints>")
    temperature: float = Field(default=0.3, ge=0, le=1, description="<constraints>Temperature controls randomness. Keep low (0.0-0.3) for logic, higher (0.7) for creativity.</constraints>")

class TranslationRequest(BaseModel):
    text: str = Field(min_length=1, max_length=100000, description="<input_context>The source text requiring translation.</input_context>")
    target_lang: str = Field(min_length=2, max_length=32, description="<constraints>The target ISO language code. Metis must translate with native fluency.</constraints>")

class CodeRequest(BaseModel):
    prompt: str = Field(min_length=1, max_length=50000, description="<input_context>The coding task specification.</input_context>")
    language: str = Field(default="python", min_length=1, max_length=32, description="<constraints>The target programming language. Must follow idiomatic standards.</constraints>")

class GrammarRequest(BaseModel):
    text: str = Field(min_length=1, max_length=100000, description="<input_context>Source text to check or transform.</input_context>")

class SummarizeRequest(BaseModel):
    text: str = Field(min_length=1, max_length=200000, description="<input_context>Source text that must be summarized without losing material facts.</input_context>")
    language: str = Field(default="auto", min_length=2, max_length=32, description="<constraints>Output language or auto to follow the source language.</constraints>")

class ActionRequest(BaseModel):
    action: str = Field(min_length=1, max_length=64, description="<critical_instructions>Supported editor action to execute.</critical_instructions>")
    text: str = Field(min_length=1, max_length=100000, description="<input_context>Selected editor text affected by the action.</input_context>")
    context: Optional[str] = Field(default="", max_length=100000, description="<input_context>Optional surrounding document context for accurate transformation.</input_context>")

class CitationRequest(BaseModel):
    text: str = Field(min_length=1, max_length=100000, description="<input_context>Claims or content requiring supporting citations.</input_context>")
    style: str = Field(default="APA", min_length=1, max_length=32, description="<constraints>Required citation formatting style such as APA or MLA.</constraints>")

class ToneRequest(BaseModel):
    text: str = Field(min_length=1, max_length=100000, description="<input_context>Source text whose tone must be transformed.</input_context>")
    tone: str = Field(min_length=1, max_length=64, description="<constraints>Target tone to apply while preserving meaning.</constraints>")
    expansion: bool = Field(default=False, description="<constraints>Whether the transformation may expand the source content.</constraints>")

class ReviewRequest(BaseModel):
    text: str = Field(min_length=1, max_length=100000, description="<input_context>Content to evaluate in the peer review workflow.</input_context>")
    criteria: Optional[List[Annotated[str, Field(min_length=1, max_length=200)]]] = Field(default=None, max_length=20, description="<constraints>Optional explicit review criteria applied to the content.</constraints>")

class SynthesisRequest(BaseModel):
    document_ids: List[Annotated[str, Field(min_length=1, max_length=128)]] = Field(min_length=1, max_length=100, description="<input_context>Authorized document identifiers used as synthesis evidence.</input_context>")
    query: str = Field(min_length=1, max_length=20000, description="<input_context>Question or synthesis objective applied to the selected documents.</input_context>")

class PlagiarismCheckRequest(BaseModel):
    content: str = Field(min_length=1, max_length=100000, description="<input_context>Content whose overlap and attribution risk must be assessed.</input_context>")

class CoverGenerateRequest(BaseModel):
    style: str = Field(default="minimalist", min_length=1, max_length=100, description="<constraints>Visual style requested for cover generation.</constraints>")

class AISuggestionRequest(BaseModel):
    context: str = Field(min_length=1, max_length=100000, description="<input_context>Document context used to generate relevant suggestions.</input_context>")

class GlossaryRequest(BaseModel):
    text: str = Field(min_length=1, max_length=200000, description="<input_context>Source text from which domain terms and definitions are extracted.</input_context>")

class StyleImitationRequest(BaseModel):
    text: str = Field(min_length=1, max_length=100000, description="<input_context>Content to rewrite while preserving its factual meaning.</input_context>")
    style_sample: str = Field(min_length=1, max_length=50000, description="<input_context>Reference sample defining the target writing characteristics.</input_context>")
    target_length: Optional[int] = Field(default=None, ge=1, le=4000, description="<constraints>Optional target output length in tokens.</constraints>")

class DraftWithMemoryRequest(BaseModel):
    prompt: str = Field(min_length=1, max_length=100000, description="<input_context>Drafting objective augmented with authenticated user memory.</input_context>")

class ExtractToStorageRequest(BaseModel):
    text: str = Field(min_length=1, max_length=200000, description="<input_context>Source content from which artifacts must be extracted.</input_context>")
    extraction_goals: List[Annotated[str, Field(min_length=1, max_length=500)]] = Field(min_length=1, max_length=20, description="<constraints>Explicit artifact extraction objectives.</constraints>")

class WebFactCheckRequest(BaseModel):
    text: str = Field(min_length=1, max_length=100000, description="<input_context>Claims to verify against current web evidence.</input_context>")

class ComplianceScreenRequest(BaseModel):
    text: str = Field(min_length=1, max_length=100000, description="<input_context>Content to evaluate against configured compliance policy.</input_context>")

class SemanticDiffRequest(BaseModel):
    text1: str = Field(min_length=1, max_length=100000, description="<input_context>Original text used as the semantic comparison baseline.</input_context>")
    text2: str = Field(min_length=1, max_length=100000, description="<input_context>Revised text compared with the semantic baseline.</input_context>")

class MemoryUserEditsRequest(BaseModel):
    action: str = Field(min_length=1, max_length=32, description="<critical_instructions>Supported memory mutation action.</critical_instructions>")
    content: str = Field(min_length=1, max_length=10000, description="<input_context>Memory content supplied by the authenticated user.</input_context>")
    memory_id: Optional[str] = Field(default=None, min_length=1, max_length=128, description="<input_context>Owned memory identifier required by update and delete actions.</input_context>")

class QuickRepliesRequest(BaseModel):
    history_messages: List[Annotated[str, Field(min_length=1, max_length=10000)]] = Field(min_length=1, max_length=50, description="<input_context>Recent bounded conversation messages used to generate replies.</input_context>")
