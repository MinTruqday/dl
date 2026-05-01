from typing import Any, List
from fastapi import APIRouter, Depends, Query
from api.dependencies import get_current_user
from models.user import UserInDB
from core.response import APIResponse
from services.reading import ReadingService
from pydantic import BaseModel

router = APIRouter(prefix="/reading")

class TypographyRequest(BaseModel):
    font_family: str
    font_size: int = 16
    line_height: float = 1.8
    letter_spacing: float = 0

class ProgressUpdate(BaseModel):
    document_id: str
    progress_percentage: float
    current_chapter_slug: str = None

class ReadingGoalCreate(BaseModel):
    target_documents: int = 0
    target_pages: int = 0
    period: str = "monthly"

class PinnedDocumentRequest(BaseModel):
    document_ids: List[str]

@router.put("/typography", response_model=APIResponse[Any])
async def update_typography(data: TypographyRequest, current_user: UserInDB = Depends(get_current_user)):
    return APIResponse(
        data=await ReadingService.update_typography(data.model_dump(), current_user),
        message="Cập nhật hiển thị thành công."
    )

@router.get("/history", response_model=APIResponse[Any])
async def get_history(skip: int = Query(0), limit: int = Query(20), current_user: UserInDB = Depends(get_current_user)):
    return APIResponse(
        data=await ReadingService.get_reading_history(current_user, skip, limit),
        message="Lấy lịch sử đọc thành công."
    )

@router.post("/progress", response_model=APIResponse[Any])
async def update_progress(data: ProgressUpdate, current_user: UserInDB = Depends(get_current_user)):
    return APIResponse(
        data=await ReadingService.update_progress(data, current_user),
        message="Cập nhật tiến độ thành công."
    )

@router.get("/continue", response_model=APIResponse[Any])
async def get_continue_reading(current_user: UserInDB = Depends(get_current_user)):
    return APIResponse(
        data=await ReadingService.get_continue_reading(current_user),
        message="Lấy danh sách đang đọc thành công."
    )

@router.post("/goals", response_model=APIResponse[Any])
async def set_reading_goal(data: ReadingGoalCreate, current_user: UserInDB = Depends(get_current_user)):
    return APIResponse(
        data=await ReadingService.set_reading_goal(data, current_user),
        message="Thiết lập mục tiêu thành công.",
        status=201
    )

@router.get("/goals", response_model=APIResponse[Any])
async def get_reading_goal(current_user: UserInDB = Depends(get_current_user)):
    return APIResponse(
        data=await ReadingService.get_reading_goal(current_user),
        message="Lấy thông tin mục tiêu thành công."
    )

@router.put("/pinned", response_model=APIResponse[Any])
async def set_pinned_documents(data: PinnedDocumentRequest, current_user: UserInDB = Depends(get_current_user)):
    return APIResponse(
        data=await ReadingService.set_pinned_documents(data.document_ids, current_user),
        message="Cập nhật danh sách ghim thành công."
    )

@router.get("/pinned", response_model=APIResponse[Any])
async def get_pinned_documents(current_user: UserInDB = Depends(get_current_user)):
    return APIResponse(
        data=await ReadingService.get_pinned_documents(current_user),
        message="Lấy danh sách đã ghim thành công."
    )

@router.get("/documents/{document_id}/search", response_model=APIResponse[Any])
async def search_in_document(document_id: str, q: str = Query(...), current_user: UserInDB = Depends(get_current_user)):
    return APIResponse(
        data=await ReadingService.search_in_document(document_id, q, current_user),
        message="Tìm kiếm trong tài liệu thành công."
    )