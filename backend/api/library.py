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
from models.library import ReadingListCreate, BookmarkFolderCreate, BookmarkFolderAssign
router = APIRouter(prefix='/thu-vien')
(prefix='/thu-vien')

@router.post('/danh-sach', response_model=APIResponse[Any])
async def create_reading_list(data: ReadingListCreate, current_user: UserInDB=Depends(get_current_user), db=Depends(get_db)):
    return APIResponse(data=await LibraryService.create_reading_list(data, current_user, db=db), message='Tạo danh sách đọc thành công', status=201)

@router.get('/danh-sach', response_model=APIResponse[Any])
async def get_my_lists(current_user: UserInDB=Depends(get_current_user), db=Depends(get_db)):
    return APIResponse(data=await LibraryService.get_my_reading_lists(current_user, db=db), message='Lấy danh sách đọc thành công')

@router.get('/danh-sach/{list_id}', response_model=APIResponse[Any])
async def get_list_by_id(list_id: str, current_user: UserInDB=Depends(get_current_user), db=Depends(get_db)):
    return APIResponse(data=await LibraryService.get_reading_list_by_id(list_id, current_user, db=db), message='Lấy chi tiết danh sách thành công')

@router.post('/danh-sach/{list_id}/tai-lieu/{document_id}', response_model=APIResponse[Any])
async def add_to_list(list_id: str, document_id: str, current_user: UserInDB=Depends(get_current_user), db=Depends(get_db)):
    return APIResponse(data=await LibraryService.add_document_to_list(list_id, document_id, current_user, db=db), message='Đã thêm vào danh sách')

@router.delete('/danh-sach/{list_id}/tai-lieu/{document_id}', response_model=APIResponse[Any])
async def remove_from_list(list_id: str, document_id: str, current_user: UserInDB=Depends(get_current_user), db=Depends(get_db)):
    return APIResponse(data=await LibraryService.remove_document_from_list(list_id, document_id, current_user, db=db), message='Đã xóa khỏi danh sách')