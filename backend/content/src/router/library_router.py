from typing import Any, List, Optional

from core.response import APIResponse
from core.schemas.user import UserInDB
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from src.router.dependency_router import get_current_user, get_db
from src.schemas.library_schema import (
    BookmarkFolderAssign,
    BookmarkFolderCreate,
    ReadingListCreate,
)
from src.services.library_service import LibraryService

router = APIRouter(prefix="/library")


@router.post("/lists", response_model=APIResponse[Any])
async def create_reading_list(
    data: ReadingListCreate,
    current_user: UserInDB = Depends(get_current_user),
    db=Depends(get_db),
):
    return APIResponse(
        data=await LibraryService.create_reading_list(data, current_user, db=db),
        message="Reading list created successfully",
        status=201,
    )


@router.get("/lists", response_model=APIResponse[Any])
async def get_my_lists(
    current_user: UserInDB = Depends(get_current_user), db=Depends(get_db)
):
    return APIResponse(
        data=await LibraryService.get_my_reading_lists(current_user, db=db),
        message="Reading list retrieved successfully",
    )


@router.get("/lists/{list_id}", response_model=APIResponse[Any])
async def get_list_by_id(
    list_id: str, current_user: UserInDB = Depends(get_current_user), db=Depends(get_db)
):
    return APIResponse(
        data=await LibraryService.get_reading_list_by_id(list_id, current_user, db=db),
        message="List details retrieved successfully",
    )


@router.post("/lists/{list_id}/documents/{document_id}", response_model=APIResponse[Any])
async def add_to_list(
    list_id: str,
    document_id: str,
    current_user: UserInDB = Depends(get_current_user),
    db=Depends(get_db),
):
    return APIResponse(
        data=await LibraryService.add_document_to_list(
            list_id, document_id, current_user, db=db
        ),
        message="Added to reading list successfully",
    )


@router.delete(
    "/lists/{list_id}/documents/{document_id}", response_model=APIResponse[Any]
)
async def remove_from_list(
    list_id: str,
    document_id: str,
    current_user: UserInDB = Depends(get_current_user),
    db=Depends(get_db),
):
    return APIResponse(
        data=await LibraryService.remove_document_from_list(
            list_id, document_id, current_user, db=db
        ),
        message="Removed from reading list successfully",
    )
