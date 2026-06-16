from typing import Any
from core.response import APIResponse
from fastapi import APIRouter, Depends, Query
from core.dependency import get_current_user, get_db
from src.schemas.highlights import HighlightCreateRequest, HighlightNoteUpdateRequest
from src.services.highlights import HighlightService

router = APIRouter(prefix="/noi-bat")

@router.post("/tai-lieu/{document_id}", response_model=APIResponse[Any])
async def create_highlight(document_id: str, data: HighlightCreateRequest, current_user: dict = Depends(get_current_user), db=Depends(get_db)):
    return APIResponse(
        data=await HighlightService.create_highlight(document_id, data.model_dump(), current_user, db=db),
        message="Yêu cầu của bạn đã được hệ thống tiếp nhận và xử lý thành công",
        status=201,
    )

@router.get("/tai-lieu/{document_id}", response_model=APIResponse[Any])
async def get_highlights(document_id: str, current_user: dict = Depends(get_current_user), db=Depends(get_db)):
    return APIResponse(
        data=await HighlightService.get_highlights(document_id, current_user, db=db),
        message="Yêu cầu của bạn đã được hệ thống tiếp nhận và xử lý thành công",
        status=200,
    )

@router.put("/{highlight_id}/ghi-chu", response_model=APIResponse[Any])
async def update_highlight_note(highlight_id: str, data: HighlightNoteUpdateRequest, current_user: dict = Depends(get_current_user), db=Depends(get_db)):
    return APIResponse(
        data=await HighlightService.update_highlight_note(highlight_id, data.note, current_user, db=db),
        message="Yêu cầu của bạn đã được hệ thống tiếp nhận và xử lý thành công",
        status=200,
    )

@router.delete("/{highlight_id}", response_model=APIResponse[Any])
async def delete_highlight(highlight_id: str, current_user: dict = Depends(get_current_user), db=Depends(get_db)):
    return APIResponse(
        data=await HighlightService.delete_highlight(highlight_id, current_user, db=db),
        message="Lỗi khi truy xuất tài liệu",
        status=200,
    )

@router.get("/ghi-chu", response_model=APIResponse[Any])
async def get_all_notes(cursor: str = Query(None), limit: int = Query(50, ge=1, le=200), skip: int = Query(0, ge=0), current_user: dict = Depends(get_current_user), db=Depends(get_db)):
    return APIResponse(
        data=await HighlightService.get_all_notes(current_user, cursor, limit, skip, db=db),
        message="Yêu cầu của bạn đã được hệ thống tiếp nhận và xử lý thành công",
        status=200,
    )

@router.get("/tai-lieu/{document_id}/ket-xuat", response_model=APIResponse[Any])
async def export_highlights_markdown(document_id: str, current_user: dict = Depends(get_current_user), db=Depends(get_db)):
    return APIResponse(
        data=await HighlightService.export_highlights_markdown(document_id, current_user, db=db),
        message="Yêu cầu của bạn đã được hệ thống tiếp nhận và xử lý thành công",
        status=200,
    )