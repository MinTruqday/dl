from typing import Any
from fastapi import APIRouter, Depends, Request, HTTPException
from core.response import APIResponse
from api.dependency import get_current_user
from models.user import UserInDB
from models.wallet import TopupRequest
import httpx

from core.config import settings
FINANCE_URL = settings.FINANCE_SERVICE_URL
router = APIRouter(prefix='/nap-tien')

async def _proxy_request(method, url, **kwargs):
    async with httpx.AsyncClient() as client:
        res = await client.request(method, f"{FINANCE_URL}{url}", **kwargs)
        if res.status_code >= 400:
            raise HTTPException(status_code=res.status_code, detail=res.json().get("detail", "Lỗi từ dịch vụ tài chính"))
        return res.json()

@router.post('/tao-link', response_model=APIResponse[Any])
async def create_deposit_link(req: TopupRequest, current_user: UserInDB=Depends(get_current_user)):
    return await _proxy_request("POST", "/nap-tien/tao-link", json=req.model_dump(), headers={"X-User-Id": str(current_user.id)})

@router.post('/payos/webhook')
async def payos_webhook(request: Request):
    payload = await request.json()
    async with httpx.AsyncClient() as client:
        res = await client.post(f"{FINANCE_URL}/nap-tien/payos/webhook", json=payload)
        return res.json()

@router.get('/kiem-tra/{order_code}', response_model=APIResponse[Any])
async def verify_deposit(order_code: int, current_user: UserInDB=Depends(get_current_user)):
    return await _proxy_request("GET", f"/nap-tien/kiem-tra/{order_code}", headers={"X-User-Id": str(current_user.id)})