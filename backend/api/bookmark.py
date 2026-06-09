from typing import Any, List, Optional
from fastapi import APIRouter, Depends, Query, Request, HTTPException, WebSocket, WebSocketDisconnect
from core.response import APIResponse
from api.dependency import get_current_user, require_role
from models.user import UserInDB, RoleEnum
from core.config import settings
import httpx
import websockets
import asyncio

CONTENT_URL = settings.CONTENT_SERVICE_URL
CONTENT_WS_URL = CONTENT_URL.replace("http://", "ws://").replace("https://", "wss://")

async def _proxy(method: str, path: str, **kwargs):
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            res = await client.request(method, f"{CONTENT_URL}{path}", **kwargs)
            if res.status_code >= 400:
                raise HTTPException(status_code=res.status_code, detail=res.json().get("detail", "Lỗi"))
            return res.json()
        except HTTPException:
            raise
        except httpx.RequestError as e:
            raise HTTPException(status_code=503, detail=f"Lỗi kết nối Content Service: {e}")

from models.user import UserInDB
router = APIRouter(prefix='/dau-trang')
(prefix='/dau-trang')

class BookmarkFolderCreate(BaseModel):
    name: str

class BookmarkFolderAssign(BaseModel):
    bookmark_ids: List[str]

@router.post('/{document_id}', response_model=APIResponse[Any])
async def toggle_bookmark(document_id: str, current_user: UserInDB=Depends(get_current_user), db=Depends(get_db)):
    return APIResponse(data=await BookmarkService.toggle_bookmark(document_id, current_user, db=db), message='Thao tác dấu trang hoàn tất', status=200)

@router.get('', response_model=APIResponse[Any])
async def get_bookmarks(limit: int=Query(100), current_user: UserInDB=Depends(get_current_user), db=Depends(get_db)):
    return APIResponse(data=await BookmarkService.get_bookmarks(current_user, limit, db=db), message='Lấy danh sách dấu trang thành công')

@router.post('/thu-muc', response_model=APIResponse[Any])
async def create_bookmark_folder(data: BookmarkFolderCreate, current_user: UserInDB=Depends(get_current_user), db=Depends(get_db)):
    return APIResponse(data=await BookmarkService.create_bookmark_folder(data.name, current_user, db=db), message='Tạo thư mục dấu trang thành công', status=201)

@router.get('/thu-muc', response_model=APIResponse[Any])
async def get_bookmark_folders(current_user: UserInDB=Depends(get_current_user), db=Depends(get_db)):
    return APIResponse(data=await BookmarkService.get_bookmark_folders(current_user, db=db), message='Lấy danh sách thư mục dấu trang thành công')

@router.put('/thu-muc/{folder_id}', response_model=APIResponse[Any])
async def assign_bookmarks(folder_id: str, data: BookmarkFolderAssign, current_user: UserInDB=Depends(get_current_user), db=Depends(get_db)):
    return APIResponse(data=await BookmarkService.assign_bookmarks_to_folder(folder_id, data.bookmark_ids, current_user, db=db), message='Cập nhật thư mục dấu trang thành công')

@router.delete('/thu-muc/{folder_id}', response_model=APIResponse[Any])
async def delete_bookmark_folder(folder_id: str, current_user: UserInDB=Depends(get_current_user), db=Depends(get_db)):
    return APIResponse(data=await BookmarkService.delete_bookmark_folder(folder_id, current_user, db=db), message='Xóa thư mục dấu trang thành công')