from typing import Any, List, Optional

from core.response import APIResponse
from core.schemas.user import UserInDB
from fastapi import APIRouter, Depends, Query, status
from pydantic import BaseModel
from src.router.dependency_router import get_current_user, get_db
from src.services.bookmark_service import BookmarkService

router = APIRouter(prefix="/dau-trang")


class BookmarkFolderCreate(BaseModel):
    name: str


class BookmarkFolderAssign(BaseModel):
    bookmark_ids: List[str]


@router.post("/{document_id}", response_model=APIResponse[Any])
async def toggle_bookmark(
    document_id: str,
    current_user: UserInDB = Depends(get_current_user),
    db=Depends(get_db),
):
    return APIResponse(
        data=await BookmarkService.toggle_bookmark(document_id, current_user, db=db),
        message="Đã hoàn tất thao tác dấu trang",
        status=200,
    )


@router.get("", response_model=APIResponse[Any])
async def get_bookmarks(
    limit: int = Query(100),
    current_user: UserInDB = Depends(get_current_user),
    db=Depends(get_db),
):
    return APIResponse(
        data=await BookmarkService.get_bookmarks(current_user, limit, db=db),
        message="Đã tải danh sách dấu trang",
    )


@router.post("/thu-muc", response_model=APIResponse[Any])
async def create_bookmark_folder(
    data: BookmarkFolderCreate,
    current_user: UserInDB = Depends(get_current_user),
    db=Depends(get_db),
):
    return APIResponse(
        data=await BookmarkService.create_bookmark_folder(
            data.name, current_user, db=db
        ),
        message="Đã tạo thư mục dấu trang",
        status=201,
    )


@router.get("/thu-muc", response_model=APIResponse[Any])
async def get_bookmark_folders(
    current_user: UserInDB = Depends(get_current_user), db=Depends(get_db)
):
    return APIResponse(
        data=await BookmarkService.get_bookmark_folders(current_user, db=db),
        message="Đã tải danh sách thư mục dấu trang",
    )


@router.put("/thu-muc/{folder_id}", response_model=APIResponse[Any])
async def assign_bookmarks(
    folder_id: str,
    data: BookmarkFolderAssign,
    current_user: UserInDB = Depends(get_current_user),
    db=Depends(get_db),
):
    return APIResponse(
        data=await BookmarkService.assign_bookmarks_to_folder(
            folder_id, data.bookmark_ids, current_user, db=db
        ),
        message="Đã cập nhật thư mục dấu trang",
    )


@router.delete("/thu-muc/{folder_id}", response_model=APIResponse[Any])
async def delete_bookmark_folder(
    folder_id: str,
    current_user: UserInDB = Depends(get_current_user),
    db=Depends(get_db),
):
    return APIResponse(
        data=await BookmarkService.delete_bookmark_folder(
            folder_id, current_user, db=db
        ),
        message="Đã xóa thư mục dấu trang",
    )
