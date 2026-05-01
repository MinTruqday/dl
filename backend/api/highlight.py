from typing import Any
from core.response import APIResponse
from fastapi import APIRouter, Depends, Query, Body
from api.dependency import get_current_user
from models.user import UserInDB
from services.highlight import HighlightService, ReadingPreferenceService
from pydantic import BaseModel

router = APIRouter(prefix="/reading")

class HighlightCreateRequest(BaseModel):
    text: str
    chapter_slug: str = ""
    color: str = "#e4e4e7"
    start_offset: int = 0
    end_offset: int = 0
    note: str = ""

class HighlightNoteUpdateRequest(BaseModel):
    note: str

class ReadingPreferenceUpdate(BaseModel):
    theme: str = "light"
    font_size: int = 16
    line_height: float = 1.8
    font_family: str = "Inter"
    is_dyslexic_mode: bool = False

@router.post("/documents/{document_id}/highlights", response_model=APIResponse[Any])
async def create_highlight(
    document_id: str,
    data: HighlightCreateRequest,
    current_user: UserInDB = Depends(get_current_user)
):
    return APIResponse(data=await HighlightService.create_highlight(document_id, data.model_dump(), current_user), message="Tạo đánh dấu đoạn văn thành công.", status=201)

@router.get("/documents/{document_id}/highlights", response_model=APIResponse[Any])
async def get_highlights(document_id: str, current_user: UserInDB = Depends(get_current_user)):
    return APIResponse(data=await HighlightService.get_highlights(document_id, current_user), message="Lấy danh sách đánh dấu của tài liệu thành công.", status=200)

@router.put("/highlights/{highlight_id}/note", response_model=APIResponse[Any])
async def update_highlight_note(
    highlight_id: str,
    data: HighlightNoteUpdateRequest,
    current_user: UserInDB = Depends(get_current_user)
):
    return APIResponse(data=await HighlightService.update_highlight_note(highlight_id, data.note, current_user), message="Cập nhật ghi chú đánh dấu thành công.", status=200)

@router.delete("/highlights/{highlight_id}", response_model=APIResponse[Any])
async def delete_highlight(highlight_id: str, current_user: UserInDB = Depends(get_current_user)):
    return APIResponse(data=await HighlightService.delete_highlight(highlight_id, current_user), message="Xóa đánh dấu đoạn văn thành công.", status=200)

@router.get("/notes", response_model=APIResponse[Any])
async def get_all_notes(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    current_user: UserInDB = Depends(get_current_user)
):
    return APIResponse(data=await HighlightService.get_all_notes(current_user, skip, limit), message="Lấy danh sách ghi chú thành công.", status=200)

@router.get("/preferences", response_model=APIResponse[Any])
async def get_reading_preferences(current_user: UserInDB = Depends(get_current_user)):
    return APIResponse(data=await ReadingPreferenceService.get_preferences(current_user), message="Lấy cài đặt tùy chỉnh đọc sách thành công.", status=200)

@router.put("/preferences", response_model=APIResponse[Any])
async def update_reading_preferences(
    data: ReadingPreferenceUpdate,
    current_user: UserInDB = Depends(get_current_user)
):
    return APIResponse(data=await ReadingPreferenceService.update_preferences(data.model_dump(), current_user), message="Cập nhật cài đặt tùy chỉnh đọc sách thành công.", status=200)

@router.get("/documents/{document_id}/highlights/export", response_model=APIResponse[Any])
async def export_highlights_markdown(
    document_id: str,
    current_user: UserInDB = Depends(get_current_user)
):
    return APIResponse(data=await HighlightService.export_highlights_markdown(document_id, current_user), message="Xuất bản danh sách đánh dấu (Markdown) thành công.", status=200)

