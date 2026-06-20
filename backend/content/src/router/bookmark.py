from typing import Any, List, Optional

from fastapi import APIRouter, Depends, Query, status
from pydantic import BaseModel
from src.router.dependency import get_current_user, get_db
from src.services.bookmark import BookmarkManager

from core.response import APIResponse
from core.dependency import CurrentUser, RoleEnum

router = APIRouter(prefix="/danh-dau")


class BookmarkFolderCreate(BaseModel):
    name: str


class BookmarkFolderAssign(BaseModel):
    bookmark_ids: List[str]


@router.post("/{document_id}", response_model=APIResponse[Any])
async def toggle_bookmark(
    document_id: str,
    current_user: CurrentUser = Depends(get_current_user),
    db=Depends(get_db),
):
    return APIResponse(
        data=await BookmarkManager.toggle_bookmark(document_id, current_user, db=db),
        message="Thao tác dấu trang thành công",
        status=200,
    )


@router.get("", response_model=APIResponse[Any])
async def get_bookmarks(
    limit: int = Query(100),
    current_user: CurrentUser = Depends(get_current_user),
    db=Depends(get_db),
):
    return APIResponse(
        data=await BookmarkManager.get_bookmarks(current_user, limit, db=db),
        message="Lấy danh sách dấu trang thành công",
    )


@router.post("/thu-muc", response_model=APIResponse[Any])
async def create_bookmark_folder(
    data: BookmarkFolderCreate,
    current_user: CurrentUser = Depends(get_current_user),
    db=Depends(get_db),
):
    return APIResponse(
        data=await BookmarkManager.create_bookmark_folder(
            data.name, current_user, db=db
        ),
        message="Tạo thư mục dấu trang thành công",
        status=201,
    )


@router.get("/thu-muc", response_model=APIResponse[Any])
async def get_bookmark_folders(
    current_user: CurrentUser = Depends(get_current_user), db=Depends(get_db)
):
    return APIResponse(
        data=await BookmarkManager.get_bookmark_folders(current_user, db=db),
        message="Lấy danh sách thư mục dấu trang thành công",
    )


@router.put("/thu-muc/{folder_id}", response_model=APIResponse[Any])
async def assign_bookmarks(
    folder_id: str,
    data: BookmarkFolderAssign,
    current_user: CurrentUser = Depends(get_current_user),
    db=Depends(get_db),
):
    return APIResponse(
        data=await BookmarkManager.assign_bookmarks_to_folder(
            folder_id, data.bookmark_ids, current_user, db=db
        ),
        message="Cập nhật thư mục dấu trang thành công",
    )


@router.delete("/thu-muc/{folder_id}", response_model=APIResponse[Any])
async def delete_bookmark_folder(
    folder_id: str,
    current_user: CurrentUser = Depends(get_current_user),
    db=Depends(get_db),
):
    return APIResponse(
        data=await BookmarkManager.delete_bookmark_folder(
            folder_id, current_user, db=db
        ),
        message="Xóa vĩnh viễn thư mục dấu trang thành công",
    )
