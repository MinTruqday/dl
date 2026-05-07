from typing import Any, List, Optional
from fastapi import APIRouter, Depends
from api.dependency import get_current_user
from models.user import UserInDB
from core.response import APIResponse
from services.library import LibraryService
from pydantic import BaseModel

router = APIRouter(prefix="/thu-vien")

class ReadingListCreate(BaseModel):
    name: str
    description: Optional[str] = None
    is_public: bool = True

class BookmarkFolderCreate(BaseModel):
    name: str

class BookmarkFolderAssign(BaseModel):
    bookmark_ids: List[str]

@router.post("/danh-sach", response_model=APIResponse[Any])
async def create_reading_list(data: ReadingListCreate, current_user: UserInDB = Depends(get_current_user)):
    return APIResponse(
        data=await LibraryService.create_reading_list(data, current_user),
        message="Tạo danh sách đọc thành công",
        status=201
    )

@router.get("/danh-sach", response_model=APIResponse[Any])
async def get_my_lists(current_user: UserInDB = Depends(get_current_user)):
    return APIResponse(
        data=await LibraryService.get_my_reading_lists(current_user),
        message="Lấy danh sách đọc thành công"
    )

@router.get("/danh-sach/{list_id}", response_model=APIResponse[Any])
async def get_list_by_id(list_id: str, current_user: UserInDB = Depends(get_current_user)):
    return APIResponse(
        data=await LibraryService.get_reading_list_by_id(list_id, current_user),
        message="Lấy chi tiết danh sách thành công"
    )

@router.post("/danh-sach/{list_id}/tai-lieu/{document_id}", response_model=APIResponse[Any])
async def add_to_list(list_id: str, document_id: str, current_user: UserInDB = Depends(get_current_user)):
    return APIResponse(
        data=await LibraryService.add_document_to_list(list_id, document_id, current_user),
        message="Đã thêm vào danh sách"
    )

@router.delete("/danh-sach/{list_id}/tai-lieu/{document_id}", response_model=APIResponse[Any])
async def remove_from_list(list_id: str, document_id: str, current_user: UserInDB = Depends(get_current_user)):
    return APIResponse(
        data=await LibraryService.remove_document_from_list(list_id, document_id, current_user),
        message="Đã xóa khỏi danh sách"
    )

@router.post("/danh-dau/thu-muc", response_model=APIResponse[Any])
async def create_bookmark_folder(data: BookmarkFolderCreate, current_user: UserInDB = Depends(get_current_user)):
    return APIResponse(
        data=await LibraryService.create_bookmark_folder(data.name, current_user),
        message="Tạo thư mục đánh dấu thành công",
        status=201
    )

@router.get("/danh-dau/thu-muc", response_model=APIResponse[Any])
async def get_bookmark_folders(current_user: UserInDB = Depends(get_current_user)):
    return APIResponse(
        data=await LibraryService.get_bookmark_folders(current_user),
        message="Lấy danh sách thư mục thành công"
    )

@router.put("/danh-dau/thu-muc/{folder_id}", response_model=APIResponse[Any])
async def assign_bookmarks(folder_id: str, data: BookmarkFolderAssign, current_user: UserInDB = Depends(get_current_user)):
    return APIResponse(
        data=await LibraryService.assign_bookmarks_to_folder(folder_id, data.bookmark_ids, current_user),
        message="Cập nhật thư mục thành công"
    )

@router.delete("/danh-dau/thu-muc/{folder_id}", response_model=APIResponse[Any])
async def delete_folder(folder_id: str, current_user: UserInDB = Depends(get_current_user)):
    return APIResponse(
        data=await LibraryService.delete_bookmark_folder(folder_id, current_user),
        message="Xóa thư mục thành công"
    )
