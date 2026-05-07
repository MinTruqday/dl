from typing import Any, Optional
from fastapi import APIRouter, Depends, Query
import json
import asyncio
from api.dependency import get_current_user
from shared.models.user import UserInDB
from shared.core.response import APIResponse
from services.ai import AIService
from pydantic import BaseModel

router = APIRouter(prefix="/tri-tue-nhan-tao", tags=["AI"])
ai_router_en = APIRouter(prefix="/ai", tags=["AI"])

@router.post("/tro-chuyen")
async def chat_streaming(data: dict, current_user: UserInDB = Depends(get_current_user)):
    from sse_starlette.sse import EventSourceResponse
    async def event_generator():
        query = data.get("query", "")
        # Giả lập phản hồi streaming từ RAG Service
        full_response = f"Tôi là trợ lý AI của DocLib. Bạn vừa hỏi: {query}. Hiện tại hệ thống RAG đang được kết nối lại."
        for chunk in full_response.split(" "):
            yield {"event": "message", "data": json.dumps({"chunk": chunk + " "})}
            await asyncio.sleep(0.05)
        yield {"data": "[DONE]"}

    return EventSourceResponse(event_generator())

# Aliases for Frontend compatibility
@ai_router_en.get("/history")
async def get_sessions_en(document_id: Optional[str] = None, current_user: UserInDB = Depends(get_current_user)):
    return await get_sessions(document_id, current_user)

@ai_router_en.post("/history")
async def create_session_en(data: dict, current_user: UserInDB = Depends(get_current_user)):
    return await create_session(data, current_user)

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

@router.get("/tim-kiem", response_model=APIResponse[Any])
async def semantic_search(q: str = Query(.), current_user: UserInDB = Depends(get_current_user)):
    return APIResponse(
        data=await AIService.semantic_search(q, current_user),
        message="Tìm kiếm ngữ nghĩa hoàn tất"
    )

@router.post("/van-ban", response_model=APIResponse[Any])
async def process_text(req: AITextRequest):
    return APIResponse(
        data=await AIService.process_text(req), 
        message="Xử lý văn bản bằng AI thành công"
    )

@router.post("/tai-lieu/{document_id}/the-ghi-nho", response_model=APIResponse[Any])
async def generate_flashcard(document_id: str, data: FlashcardRequest, current_user: UserInDB = Depends(get_current_user)):
    return APIResponse(
        data=await AIService.generate_flashcard(document_id, data.text, data.context, current_user),
        message="Tạo flashcard thành công",
        status=201
    )

@router.post("/the-ghi-nho/on-tap", response_model=APIResponse[Any])
async def review_flashcard(data: FlashcardReviewRequest, current_user: UserInDB = Depends(get_current_user)):
    return APIResponse(
        data=await AIService.review_flashcard(data.card_id, data.quality, current_user),
        message="Đã ghi nhận ôn tập"
    )

@router.get("/lich-su", response_model=APIResponse[Any])
async def get_sessions(document_id: Optional[str] = None, current_user: UserInDB = Depends(get_current_user)):
    from services.rag import RagService
    return APIResponse(
        data=await RagService.get_user_sessions(str(current_user.id), document_id),
        message="Lấy lịch sử hội thoại thành công"
    )

@router.post("/lich-su", response_model=APIResponse[Any])
async def create_session(data: dict, current_user: UserInDB = Depends(get_current_user)):
    from services.rag import RagService
    return APIResponse(
        data=await RagService.create_session(str(current_user.id), data.get("document_id"), data.get("first_query", "")),
        message="Khởi tạo hội thoại mới thành công",
        status=201
    )

@router.put("/lich-su/{session_id}/tieu-de", response_model=APIResponse[Any])
async def update_title(session_id: str, data: dict, current_user: UserInDB = Depends(get_current_user)):
    from services.rag import RagService
    success = await RagService.update_title(session_id, data.get("title", ""), str(current_user.id))
    if not success: from fastapi import HTTPException; raise HTTPException(status_code=404, detail="Không tìm thấy hội thoại")
    return APIResponse(data={}, message="Cập nhật tiêu đề thành công")

@router.delete("/lich-su/{session_id}", response_model=APIResponse[Any])
async def delete_session(session_id: str, current_user: UserInDB = Depends(get_current_user)):
    from services.rag import RagService
    success = await RagService.delete_session(session_id, str(current_user.id))
    if not success: from fastapi import HTTPException; raise HTTPException(status_code=404, detail="Không tìm thấy hội thoại")
    return APIResponse(data={}, message="Xóa hội thoại thành công")
