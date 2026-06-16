from typing import Any, List
from core.response import APIResponse
from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from core.dependency import get_current_user, get_db
from src.services.bookmarks import BookmarkService

router = APIRouter(prefix="/danh-dau")

class BookmarkFolderCreate(BaseModel):
    name: str

class BookmarkFolderAssign(BaseModel):
    bookmark_ids: List[str]

@router.post("/{document_id}", response_model=APIResponse[Any])
async def toggle_bookmark(document_id: str, current_user: dict = Depends(get_current_user), db=Depends(get_db)):
    return APIResponse(
        data=await BookmarkService.toggle_bookmark(document_id, current_user, db=db),
        message="Yêu cầu của bạn đã được hệ thống tiếp nhận và xử lý thành công",
        status=200,
    )

@router.get("", response_model=APIResponse[Any])
async def get_bookmarks(limit: int = Query(100), current_user: dict = Depends(get_current_user), db=Depends(get_db)):
    return APIResponse(
        data=await BookmarkService.get_bookmarks(current_user, limit, db=db),
        message="Yêu cầu của bạn đã được hệ thống tiếp nhận và xử lý thành công",
    )

@router.post("/thu-muc", response_model=APIResponse[Any])
async def create_bookmark_folder(data: BookmarkFolderCreate, current_user: dict = Depends(get_current_user), db=Depends(get_db)):
    return APIResponse(
        data=await BookmarkService.create_bookmark_folder(data.name, current_user, db=db),
        message="Yêu cầu của bạn đã được hệ thống tiếp nhận và xử lý thành công",
        status=201,
    )

@router.get("/thu-muc", response_model=APIResponse[Any])
async def get_bookmark_folders(current_user: dict = Depends(get_current_user), db=Depends(get_db)):
    return APIResponse(
        data=await BookmarkService.get_bookmark_folders(current_user, db=db),
        message="Yêu cầu của bạn đã được hệ thống tiếp nhận và xử lý thành công",
    )

@router.put("/thu-muc/{folder_id}", response_model=APIResponse[Any])
async def assign_bookmarks(folder_id: str, data: BookmarkFolderAssign, current_user: dict = Depends(get_current_user), db=Depends(get_db)):
    return APIResponse(
        data=await BookmarkService.assign_bookmarks_to_folder(folder_id, data.bookmark_ids, current_user, db=db),
        message="Yêu cầu của bạn đã được hệ thống tiếp nhận và xử lý thành công",
    )

@router.delete("/thu-muc/{folder_id}", response_model=APIResponse[Any])
async def delete_bookmark_folder(folder_id: str, current_user: dict = Depends(get_current_user), db=Depends(get_db)):
    return APIResponse(
        data=await BookmarkService.delete_bookmark_folder(folder_id, current_user, db=db),
        message="Hệ thống đang tiến hành xử lý dữ liệu theo yêu cầu của bạn",
    )