from typing import Any

from src.core.logging_route import LoggingRoute
from fastapi import APIRouter, Depends, Query
from src.api.dependency import get_current_user, get_db
from src.schemas.highlight import (
    HighlightCreateRequest,
    HighlightNoteUpdateRequest,
    ReadingPreferenceUpdate,
)
from src.services.highlight import HighlightService

from src.core.response import APIResponse
from src.core.dependency import CurrentUser, Role

router = APIRouter(route_class=LoggingRoute, prefix="/danh-dau")

@router.post("/tai-lieu/{document_id}", response_model=APIResponse[Any])
async def create_highlight(
    document_id: str,
    data: HighlightCreateRequest,
    current_user: CurrentUser = Depends(get_current_user),
    db=Depends(get_db),
):
    return APIResponse(
        data=await HighlightService.create_highlight(
            document_id, data.model_dump(), current_user
        ),
        message="Khởi tạo đoạn văn bản đánh dấu hoàn tất",
        status=201,
    )

@router.get("/tai-lieu/{document_id}", response_model=APIResponse[Any])
async def get_highlights(
    document_id: str,
    current_user: CurrentUser = Depends(get_current_user),
    db=Depends(get_db),
):
    return APIResponse(
        data=await HighlightService.get_highlights(document_id, current_user),
        message="Trích xuất danh sách đoạn văn bản đánh dấu hoàn tất",
        status=200,
    )

@router.put("/{highlight_id}/ghi-chu", response_model=APIResponse[Any])
async def update_highlight_note(
    highlight_id: str,
    data: HighlightNoteUpdateRequest,
    current_user: CurrentUser = Depends(get_current_user),
    db=Depends(get_db),
):
    return APIResponse(
        data=await HighlightService.update_highlight_note(
            highlight_id, data.note, current_user
        ),
        message="Cập nhật nội dung ghi chú cho phần đánh dấu hoàn tất",
        status=200,
    )

@router.delete("/{highlight_id}", response_model=APIResponse[Any])
async def delete_highlight(
    highlight_id: str,
    current_user: CurrentUser = Depends(get_current_user),
    db=Depends(get_db),
):
    return APIResponse(
        data=await HighlightService.delete_highlight(highlight_id, current_user),
        message="Hủy bỏ đoạn văn bản đánh dấu khỏi tài liệu hoàn tất",
        status=200,
    )

@router.get("/ghi-chu", response_model=APIResponse[Any])
async def get_all_notes(
    cursor: str = Query(None),
    limit: int = Query(50, ge=1, le=200),
    skip: int = Query(0, ge=0),
    current_user: CurrentUser = Depends(get_current_user),
    db=Depends(get_db),
):
    return APIResponse(
        data=await HighlightService.get_all_notes(
            current_user, cursor, limit, skip
        ),
        message="Trích xuất danh sách toàn bộ ghi chú cá nhân hoàn tất",
        status=200,
    )

@router.get("/tai-lieu/{document_id}/ket-xuat", response_model=APIResponse[Any])
async def export_highlights_markdown(
    document_id: str,
    current_user: CurrentUser = Depends(get_current_user),
    db=Depends(get_db),
):
    return APIResponse(
        data=await HighlightService.export_highlights_markdown(
            document_id, current_user
        ),
        message="Kết xuất dữ liệu đoạn văn bản đánh dấu hoàn tất",
        status=200,
    )
