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
from models.library import PinnedDocumentRequest
router = APIRouter(prefix='/ghim')
(prefix='/ghim', tags=['Pin'])

@router.get('', response_model=APIResponse[Any])
async def get_pinned_documents(current_user: UserInDB=Depends(get_current_user), db=Depends(get_db)):
    return APIResponse(data=await PinService.get_pinned_documents(current_user, db=db), message='Lấy danh sách ghim thành công')

@router.post('/{document_id}', response_model=APIResponse[Any])
async def pin_document(document_id: str, current_user: UserInDB=Depends(get_current_user), db=Depends(get_db)):
    return APIResponse(data=await PinService.pin_document(document_id, current_user, db=db), message='Ghim tài liệu thành công')

@router.delete('/{document_id}', response_model=APIResponse[Any])
async def unpin_document(document_id: str, current_user: UserInDB=Depends(get_current_user), db=Depends(get_db)):
    return APIResponse(data=await PinService.unpin_document(document_id, current_user, db=db), message='Bỏ ghim tài liệu thành công')

@router.put('', response_model=APIResponse[Any])
async def set_pinned_documents(data: PinnedDocumentRequest, current_user: UserInDB=Depends(get_current_user), db=Depends(get_db)):
    return APIResponse(data=await PinService.set_pinned_documents(data.document_ids, current_user, db=db), message='Cập nhật danh sách ghim thành công')