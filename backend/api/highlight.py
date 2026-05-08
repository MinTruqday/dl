from typing import Any
from fastapi import APIRouter, Depends, Query
from api.dependency import get_current_user
from models.user import UserInDB
from models.highlight import HighlightCreateRequest, HighlightNoteUpdateRequest, ReadingPreferenceUpdate
from services.highlight import HighlightService, ReadingPreferenceService
from core.response import APIResponse

router = APIRouter(prefix="/doc-tai-lieu")

@router.post("/tai-lieu/{document_id}/danh-dau", response_model=APIResponse[Any])
async def create_highlight(
    document_id: str,
    data: HighlightCreateRequest,
    current_user: UserInDB = Depends(get_current_user)
):
    return APIResponse(data=await HighlightService.create_highlight(document_id, data.model_dump(), current_user), message="Tạo đánh dấu đoạn văn thành công", status=201)

@router.get("/tai-lieu/{document_id}/danh-dau", response_model=APIResponse[Any])
async def get_highlights(document_id: str, current_user: UserInDB = Depends(get_current_user)):
    return APIResponse(data=await HighlightService.get_highlights(document_id, current_user), message="Lấy danh sách đánh dấu của tài liệu thành công", status=200)

@router.put("/danh-dau/{highlight_id}/ghi-chu", response_model=APIResponse[Any])
async def update_highlight_note(
    highlight_id: str,
    data: HighlightNoteUpdateRequest,
    current_user: UserInDB = Depends(get_current_user)
):
    return APIResponse(data=await HighlightService.update_highlight_note(highlight_id, data.note, current_user), message="Cập nhật ghi chú đánh dấu thành công", status=200)

@router.delete("/danh-dau/{highlight_id}", response_model=APIResponse[Any])
async def delete_highlight(highlight_id: str, current_user: UserInDB = Depends(get_current_user)):
    return APIResponse(data=await HighlightService.delete_highlight(highlight_id, current_user), message="Xóa đánh dấu đoạn văn thành công", status=200)

@router.get("/ghi-chu", response_model=APIResponse[Any])
async def get_all_notes(
    cursor: str = Query(None),
    limit: int = Query(50, ge=1, le=200),
    current_user: UserInDB = Depends(get_current_user)
):
    return APIResponse(data=await HighlightService.get_all_notes(current_user, cursor, limit), message="Lấy danh sách ghi chú thành công", status=200)

@router.get("/tuy-chinh", response_model=APIResponse[Any])
async def get_reading_preferences(current_user: UserInDB = Depends(get_current_user)):
    return APIResponse(data=await ReadingPreferenceService.get_preferences(current_user), message="Lấy cài đặt tùy chỉnh đọc sách thành công", status=200)

@router.put("/tuy-chinh", response_model=APIResponse[Any])
async def update_reading_preferences(
    data: ReadingPreferenceUpdate,
    current_user: UserInDB = Depends(get_current_user)
):
    return APIResponse(data=await ReadingPreferenceService.update_preferences(data.model_dump(), current_user), message="Cập nhật cài đặt tùy chỉnh đọc sách thành công", status=200)

@router.get("/tai-lieu/{document_id}/danh-dau/xuat-tai-lieu", response_model=APIResponse[Any])
async def export_highlights_markdown(
    document_id: str,
    current_user: UserInDB = Depends(get_current_user)
):
    return APIResponse(data=await HighlightService.export_highlights_markdown(document_id, current_user), message="Xuất bản danh sách đánh dấu (Markdown) thành công", status=200)

