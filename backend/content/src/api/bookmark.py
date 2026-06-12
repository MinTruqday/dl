from typing import Any, List, Optional
from fastapi import APIRouter, Depends, status, Query
from core.response import APIResponse
from src.api.dependency import get_db, get_current_user
from src.schemas.user import UserInDB
from src.services.bookmark import BookmarkService
from pydantic import BaseModel
router = APIRouter(prefix='/dau-trang')

class BookmarkFolderCreate(BaseModel):
    name: str

class BookmarkFolderAssign(BaseModel):
    bookmark_ids: List[str]

@router.post('/{document_id}', response_model=APIResponse[Any])
async def toggle_bookmark(document_id: str, current_user: UserInDB=Depends(get_current_user), db=Depends(get_db)):
    return APIResponse(data=await BookmarkService.toggle_bookmark(document_id, current_user, db=db), message='Thao tác dấu trang success', status=200)

@router.get('', response_model=APIResponse[Any])
async def get_bookmarks(limit: int=Query(100), current_user: UserInDB=Depends(get_current_user), db=Depends(get_db)):
    return APIResponse(data=await BookmarkService.get_bookmarks(current_user, limit, db=db), message='Lấy danh sách dấu trang success')

@router.post('/thu-muc', response_model=APIResponse[Any])
async def create_bookmark_folder(data: BookmarkFolderCreate, current_user: UserInDB=Depends(get_current_user), db=Depends(get_db)):
    return APIResponse(data=await BookmarkService.create_bookmark_folder(data.name, current_user, db=db), message='Tạo thư mục dấu trang success', status=201)

@router.get('/thu-muc', response_model=APIResponse[Any])
async def get_bookmark_folders(current_user: UserInDB=Depends(get_current_user), db=Depends(get_db)):
    return APIResponse(data=await BookmarkService.get_bookmark_folders(current_user, db=db), message='Lấy danh sách thư mục dấu trang success')

@router.put('/thu-muc/{folder_id}', response_model=APIResponse[Any])
async def assign_bookmarks(folder_id: str, data: BookmarkFolderAssign, current_user: UserInDB=Depends(get_current_user), db=Depends(get_db)):
    return APIResponse(data=await BookmarkService.assign_bookmarks_to_folder(folder_id, data.bookmark_ids, current_user, db=db), message='Cập nhật thư mục dấu trang success')

@router.delete('/thu-muc/{folder_id}', response_model=APIResponse[Any])
async def delete_bookmark_folder(folder_id: str, current_user: UserInDB=Depends(get_current_user), db=Depends(get_db)):
    return APIResponse(data=await BookmarkService.delete_bookmark_folder(folder_id, current_user, db=db), message='Xóa thư mục dấu trang success')