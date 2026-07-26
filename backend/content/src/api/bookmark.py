from typing import Any, List, Optional

from src.core.logging_route import LoggingRoute
from fastapi import APIRouter, Depends, Query, status
from src.schemas.library import BookmarkFolderCreate, BookmarkFolderAssign
from src.api.dependency import get_current_user, get_db
from src.services.bookmark import BookmarkService

from src.core.response import APIResponse
from src.core.dependency import CurrentUser, Role

router = APIRouter(route_class=LoggingRoute, prefix="/dau-trang")

@router.post("/thu-muc", response_model=APIResponse[Any], status_code=201)
async def create_bookmark_folder(
    data: BookmarkFolderCreate,
    current_user: CurrentUser = Depends(get_current_user),
    db=Depends(get_db),
):
    return APIResponse(
        data=await BookmarkService.create_bookmark_folder(
            data.name, current_user
        ),
        message="Khởi tạo thư mục dấu trang hoàn tất",
        status=201,
    )

@router.get("/thu-muc", response_model=APIResponse[Any])
async def get_bookmark_folders(
    current_user: CurrentUser = Depends(get_current_user), db=Depends(get_db)
):
    return APIResponse(
        data=await BookmarkService.get_bookmark_folders(current_user),
        message="Trích xuất danh sách thư mục dấu trang hoàn tất",
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
        message="Đồng bộ hóa thư mục dấu trang hoàn tất",
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
        message="Hủy bỏ hoàn toàn thư mục dấu trang hoàn tất",
    )

@router.post("/{document_id}", response_model=APIResponse[Any])
async def toggle_bookmark(
    document_id: str,
    current_user: CurrentUser = Depends(get_current_user),
    db=Depends(get_db),
):
    return APIResponse(
        data=await BookmarkService.toggle_bookmark(document_id, current_user),
        message="Xử lý thao tác dấu trang tài liệu hoàn tất",
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
        message="Trích xuất danh sách dấu trang hoàn tất",
    )
