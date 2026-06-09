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

from models.user import UserInDB, RoleEnum
from models.document import ModerateDocumentRequest
router = APIRouter(prefix='/ban-nhap')
(prefix='/ban-nhap')

@router.get('/hang-doi', response_model=APIResponse[Any], dependencies=[Depends(require_role([RoleEnum.MODERATOR, RoleEnum.ADMIN]))])
async def get_approval_queue(cursor: str=None, limit: int=30, db=Depends(get_db)):
    return APIResponse(data=await DocumentService.get_approval_queue(cursor, limit, db=db), message='Lấy hàng đợi phê duyệt thành công')

@router.post('/{document_id}/kiem-duyet', response_model=APIResponse[Any], dependencies=[Depends(require_role([RoleEnum.MODERATOR, RoleEnum.ADMIN]))])
async def moderate_document(document_id: str, req: ModerateDocumentRequest, current_user: UserInDB=Depends(get_current_user), db=Depends(get_db)):
    return APIResponse(data=await DocumentService.moderate_document(document_id, req.action, req.reason, current_user, db=db), message='Xử lý tài liệu thành công')