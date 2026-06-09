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
router = APIRouter(prefix='/phien-ban')
(prefix='/phien-ban')

@router.post('/luu/{document_id}', response_model=APIResponse[Any])
async def save_version(document_id: str, version_note: str, current_user: UserInDB=Depends(get_current_user), db=Depends(get_db)):
    return APIResponse(data=await VersionsService.save_version(document_id, version_note, current_user, db=db), message='Lưu phiên bản tài liệu thành công', status=201)

@router.get('/tai-lieu/{document_id}', response_model=APIResponse[Any])
async def get_document_versions(document_id: str, current_user: UserInDB=Depends(get_current_user), db=Depends(get_db)):
    return APIResponse(data=await VersionsService.get_versions(document_id, current_user, db=db), message='Lấy danh sách phiên bản thành công')

@router.post('/{version_id}/khoi-phuc', response_model=APIResponse[Any])
async def restore_version(version_id: str, current_user: UserInDB=Depends(get_current_user), db=Depends(get_db)):
    return APIResponse(data=await VersionsService.restore_version(version_id, current_user, db=db), message='Khôi phục phiên bản thành công')