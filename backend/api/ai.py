from typing import Any, Optional
from fastapi import APIRouter, Depends, Query
from api.dependencies import get_current_user
from models.user import UserInDB
from core.response import APIResponse
from services.ai_assistant import AIAssistantService
from pydantic import BaseModel

router = APIRouter(prefix="/ai")

class AITextRequest(BaseModel):
    text: str
    action: str
    context: Optional[str] = ""
    target_lang: Optional[str] = "Vietnamese"

class FlashcardRequest(BaseModel):
    text: str
    context: str = ""

class FlashcardReviewRequest(BaseModel):
    card_id: str
    quality: int

@router.get("/search", response_model=APIResponse[Any])
async def semantic_search(q: str = Query(...), current_user: UserInDB = Depends(get_current_user)):
    return APIResponse(
        data=await AIAssistantService.semantic_search(q, current_user),
        message="Tìm kiếm ngữ nghĩa hoàn tất."
    )

@router.post("/text", response_model=APIResponse[Any])
async def process_text(req: AITextRequest):
    return APIResponse(
        data=await AIAssistantService.process_text(req), 
        message="Xử lý văn bản bằng AI thành công."
    )

@router.post("/documents/{document_id}/flashcards", response_model=APIResponse[Any])
async def generate_flashcard(document_id: str, data: FlashcardRequest, current_user: UserInDB = Depends(get_current_user)):
    return APIResponse(
        data=await AIAssistantService.generate_flashcard(document_id, data.text, data.context, current_user),
        message="Tạo flashcard thành công.",
        status=201
    )

@router.post("/flashcards/review", response_model=APIResponse[Any])
async def review_flashcard(data: FlashcardReviewRequest, current_user: UserInDB = Depends(get_current_user)):
    return APIResponse(
        data=await AIAssistantService.review_flashcard(data.card_id, data.quality, current_user),
        message="Đã ghi nhận ôn tập."
    )
