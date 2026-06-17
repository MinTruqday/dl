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

router = APIRouter(prefix="/bookmarks")


@router.post("/documents/{document_id}", response_model=APIResponse[Any])
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
        message="The new highlighted segment has been successfully created and attached to the document",
        status=201,
    )


@router.get("/documents/{document_id}", response_model=APIResponse[Any])
async def get_highlights(
    document_id: str,
    current_user: UserInDB = Depends(get_current_user),
    db=Depends(get_db),
):
    return APIResponse(
        data=await HighlightService.get_highlights(document_id, current_user, db=db),
        message="The requested highlighted segments have been successfully retrieved from the document",
        status=200,
    )


@router.put("/{highlight_id}/notes", response_model=APIResponse[Any])
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
        message="The personal note attached to the highlighted segment has been successfully updated",
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
        message="The specified highlighted segment has been permanently removed from the document",
        status=200,
    )


@router.get("/notes", response_model=APIResponse[Any])
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
        message="The list of personal notes has been successfully retrieved from the system records",
        status=200,
    )


@router.get("/documents/{document_id}/export", response_model=APIResponse[Any])
async def export_highlights_markdown(
    document_id: str,
    current_user: UserInDB = Depends(get_current_user),
    db=Depends(get_db),
):
    return APIResponse(
        data=await HighlightService.export_highlights_markdown(
            document_id, current_user, db=db
        ),
        message="The list of highlighted segments has been successfully compiled and exported",
        status=200,
    )