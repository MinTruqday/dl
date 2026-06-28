from typing import Any, List, Optional

from src.core.logging_route import LoggingRoute
from fastapi import APIRouter, Depends, Query, status
from src.schemas.library import BookmarkFolderCreate, BookmarkFolderAssign
from src.api.dependency import get_current_user, get_db
from src.services.bookmark import BookmarkService

from src.core.response import APIResponse
from src.core.dependency import CurrentUser, Role

router = APIRouter(route_class=LoggingRoute, prefix="/danh-dau")

@router.post("/thu-muc", response_model=APIResponse[Any])
async def create_bookmark_folder(
    data: BookmarkFolderCreate,
    current_user: CurrentUser = Depends(get_current_user),
    db=Depends(get_db),
):
    return APIResponse(
        data=await BookmarkService.create_bookmark_folder(
            data.name, current_user
        ),
        message="Tạo thư mục dấu trang thành công",
        status=201,
    )

@router.get("/thu-muc", response_model=APIResponse[Any])
async def get_bookmark_folders(
    current_user: CurrentUser = Depends(get_current_user), db=Depends(get_db)
):
    return APIResponse(
        data=await BookmarkService.get_bookmark_folders(current_user),
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
        data=await BookmarkService.assign_bookmarks_to_folder(
            folder_id, data.document_ids, current_user
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
        data=await BookmarkService.delete_bookmark_folder(
            folder_id, current_user
        ),
        message="Xóa vĩnh viễn thư mục dấu trang thành công",
    )

@router.post("/{document_id}", response_model=APIResponse[Any])
async def toggle_bookmark(
    document_id: str,
    current_user: CurrentUser = Depends(get_current_user),
    db=Depends(get_db),
):
    return APIResponse(
        data=await BookmarkService.toggle_bookmark(document_id, current_user),
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
        data=await BookmarkService.get_bookmarks(current_user, limit),
        message="Lấy danh sách dấu trang thành công",
    )

