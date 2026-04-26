from fastapi import APIRouter, Depends
from pydantic import BaseModel
from typing import Optional
from services.agent import AgentService

router = APIRouter()

class AITextRequest(BaseModel):
    text: str
    action: str
    context: Optional[str] = ""
    target_lang: Optional[str] = "Vietnamese"

class AIDocumentRequest(BaseModel):
    text: str
    action: str
    context: Optional[str] = ""

@router.post("/text")
async def process_text(req: AITextRequest):
    return await AgentService.process_text(req)

@router.post("/document")
async def process_document(req: AIDocumentRequest):
    return await AgentService.process_document(req)

