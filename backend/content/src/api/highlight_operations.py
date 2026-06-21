from typing import Any

from fastapi import APIRouter, Depends, Query
from src.api.system_dependency import get_current_user, get_db
from src.schemas.highlight import (
    HighlightCreateRequest,
    HighlightNoteUpdateRequest,
    ReadingPreferenceUpdate,
)
from src.services.highlight_operations import HighlightOperations

from core.api_response import APIResponse
from core.system_dependency import CurrentUser, RoleEnum

router = APIRouter(prefix="/danh-dau")


@router.post("/tai-lieu/{document_id}", response_model=APIResponse[Any])
async def create_highlight(
    document_id: str,
    data: HighlightCreateRequest,
    current_user: CurrentUser = Depends(get_current_user),
    db=Depends(get_db),
):
    return APIResponse(
        data=await HighlightOperations.create_highlight(
            document_id, data.model_dump(), current_user, db=db
        ),
        message="Tạo đoạn văn bản nổi bật thành công",
        status=201,
    )


@router.get("/tai-lieu/{document_id}", response_model=APIResponse[Any])
async def get_highlights(
    document_id: str,
    current_user: CurrentUser = Depends(get_current_user),
    db=Depends(get_db),
):
    return APIResponse(
        data=await HighlightOperations.get_highlights(document_id, current_user, db=db),
        message="Lấy đoạn văn bản nổi bật thành công",
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
        data=await HighlightOperations.update_highlight_note(
            highlight_id, data.note, current_user, db=db
        ),
        message="Cập nhật ghi chú thành công",
        status=200,
    )


@router.delete("/{highlight_id}", response_model=APIResponse[Any])
async def delete_highlight(
    highlight_id: str,
    current_user: CurrentUser = Depends(get_current_user),
    db=Depends(get_db),
):
    return APIResponse(
        data=await HighlightOperations.delete_highlight(highlight_id, current_user, db=db),
        message="Đã xóa phần đánh dấu khỏi tài liệu",
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
        data=await HighlightOperations.get_all_notes(
            current_user, cursor, limit, skip, db=db
        ),
        message="Lấy danh sách ghi chú cá nhân thành công",
        status=200,
    )


@router.get("/tai-lieu/{document_id}/ket-xuat", response_model=APIResponse[Any])
async def export_highlights_markdown(
    document_id: str,
    current_user: CurrentUser = Depends(get_current_user),
    db=Depends(get_db),
):
    return APIResponse(
        data=await HighlightOperations.export_highlights_markdown(
            document_id, current_user, db=db
        ),
        message="Lấy danh sách đoạn văn bản đánh dấu thành công",
        status=200,
    )
