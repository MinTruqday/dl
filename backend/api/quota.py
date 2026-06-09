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
from models.quota import QuotaLimit
router = APIRouter(prefix='/quota')
(prefix='/quota', tags=['Quota'])

@router.get('/me', response_model=APIResponse[Any])
async def get_my_quota(current_user: UserInDB=Depends(get_current_user), db=Depends(get_db)):
    usage = await QuotaService.get_current_usage(str(current_user.id), current_user.role.value, db=db)
    return APIResponse(data=usage, message='Lấy thông tin hạn mức thành công')

@router.put('/config/{role}', response_model=APIResponse[Any])
async def update_role_quota(role: str, limits: QuotaLimit, current_user: UserInDB=Depends(require_role([RoleEnum.ADMIN])), db=Depends(get_db)):
    result = await QuotaService.update_global_limits(role, limits, db=db)
    return APIResponse(data=result, message='Cập nhật cấu hình hạn mức thành công')

@router.get('/config', response_model=APIResponse[Any])
async def get_global_config(current_user: UserInDB=Depends(require_role([RoleEnum.ADMIN])), db=Depends(get_db)):
    config = await QuotaService._get_global_config(db=db)
    return APIResponse(data=config.role_limits, message='Lấy cấu hình hạn mức thành công')