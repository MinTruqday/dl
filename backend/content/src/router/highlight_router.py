from typing import Any

from core.response import APIResponse
from core.schemas.user import UserInDB
from fastapi import APIRouter, Depends, Query
from src.router.dependency_router import get_current_user, get_db
from src.schemas.highlight_schema import (
    HighlightCreateRequest,
    HighlightNoteUpdateRequest,
    ReadingPreferenceUpdate,
)
from src.services.highlight_service import HighlightService

router = APIRouter(prefix="/danh-dau")


@router.post("/tai-lieu/{document_id}", response_model=APIResponse[Any])
async def create_highlight(
    document_id: str,
    data: HighlightCreateRequest,
    current_user: UserInDB = Depends(get_current_user),
    db=Depends(get_db),
):
    return APIResponse(
        data=await HighlightService.create_highlight(
            document_id, data.model_dump(), current_user, db=db
        ),
        message="Đã tạo đánh dấu đoạn văn",
        status=201,
    )


@router.get("/tai-lieu/{document_id}", response_model=APIResponse[Any])
async def get_highlights(
    document_id: str,
    current_user: UserInDB = Depends(get_current_user),
    db=Depends(get_db),
):
    return APIResponse(
        data=await HighlightService.get_highlights(document_id, current_user, db=db),
        message="Đã tải danh sách các đoạn được đánh dấu",
        status=200,
    )


@router.put("/{highlight_id}/ghi-chu", response_model=APIResponse[Any])
async def update_highlight_note(
    highlight_id: str,
    data: HighlightNoteUpdateRequest,
    current_user: UserInDB = Depends(get_current_user),
    db=Depends(get_db),
):
    return APIResponse(
        data=await HighlightService.update_highlight_note(
            highlight_id, data.note, current_user, db=db
        ),
        message="Đã cập nhật ghi chú cho đoạn đánh dấu",
        status=200,
    )


@router.delete("/{highlight_id}", response_model=APIResponse[Any])
async def delete_highlight(
    highlight_id: str,
    current_user: UserInDB = Depends(get_current_user),
    db=Depends(get_db),
):
    return APIResponse(
        data=await HighlightService.delete_highlight(highlight_id, current_user, db=db),
        message="Đã xóa đánh dấu đoạn văn",
        status=200,
    )


@router.get("/ghi-chu", response_model=APIResponse[Any])
async def get_all_notes(
    cursor: str = Query(None),
    limit: int = Query(50, ge=1, le=200),
    skip: int = Query(0, ge=0),
    current_user: UserInDB = Depends(get_current_user),
    db=Depends(get_db),
):
    return APIResponse(
        data=await HighlightService.get_all_notes(
            current_user, cursor, limit, skip, db=db
        ),
        message="Đã tải danh sách ghi chú",
        status=200,
    )


@router.get("/tai-lieu/{document_id}/ket-xuat", response_model=APIResponse[Any])
async def export_highlights_markdown(
    document_id: str,
    current_user: UserInDB = Depends(get_current_user),
    db=Depends(get_db),
):
    return APIResponse(
        data=await HighlightService.export_highlights_markdown(
            document_id, current_user, db=db
        ),
        message="Đã xuất danh sách các đoạn đánh dấu",
        status=200,
    )
