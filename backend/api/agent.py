from typing import Any
from core.response import APIResponse
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

@router.post("/text", response_model=APIResponse[Any])
async def process_text(req: AITextRequest):
    return APIResponse(data=await AgentService.process_text(req), message="Xử lý văn bản bằng AI thành công.", status=200)

@router.post("/document", response_model=APIResponse[Any])
async def process_document(req: AIDocumentRequest):
    return APIResponse(data=await AgentService.process_document(req), message="Phân tích tài liệu bằng AI thành công.", status=200)

