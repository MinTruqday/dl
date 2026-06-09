from typing import Any
from core.response import APIResponse
from fastapi import APIRouter, Depends, Query, HTTPException
from api.dependency import get_current_user
from models.user import UserInDB
from models.wallet import RedeemVoucherRequest, TipRequest
import httpx

from core.config import settings
FINANCE_URL = settings.FINANCE_SERVICE_URL
router = APIRouter(prefix='/vi-tien')

async def _proxy_request(method, url, **kwargs):
    async with httpx.AsyncClient() as client:
        res = await client.request(method, f"{FINANCE_URL}{url}", **kwargs)
        if res.status_code >= 400:
            raise HTTPException(status_code=res.status_code, detail=res.json().get("detail", "Lỗi từ dịch vụ tài chính"))
        return res.json()

@router.get('/so-du', response_model=APIResponse[Any])
async def get_balance(current_user: UserInDB=Depends(get_current_user)):
    return await _proxy_request("GET", "/vi-tien/so-du", headers={"X-User-Id": str(current_user.id)})

@router.post('/ma-qua-tang/doi-ma', response_model=APIResponse[Any])
async def redeem_voucher(req: RedeemVoucherRequest, current_user: UserInDB=Depends(get_current_user)):
    return await _proxy_request("POST", "/vi-tien/ma-qua-tang/doi-ma", json=req.model_dump(), headers={"X-User-Id": str(current_user.id)})

@router.get('/lich-su', response_model=APIResponse[Any])
async def get_history(cursor: str=Query(None), limit: int=Query(30, ge=1, le=100), tx_type: str=Query(None), skip: int=Query(0, ge=0), current_user: UserInDB=Depends(get_current_user)):
    params = {"cursor": cursor, "limit": limit, "tx_type": tx_type, "skip": skip}
    params = {k: v for k, v in params.items() if v is not None}
    return await _proxy_request("GET", "/vi-tien/lich-su", params=params, headers={"X-User-Id": str(current_user.id)})

@router.post('/tien-ung-ho/{target_user_id}', response_model=APIResponse[Any])
async def virtual_tip(target_user_id: str, req: TipRequest, current_user: UserInDB=Depends(get_current_user)):
    return await _proxy_request("POST", f"/vi-tien/tien-ung-ho/{target_user_id}", json=req.model_dump(), headers={"X-User-Id": str(current_user.id)})

@router.get('/nguoi-ung-ho-hang-dau', response_model=APIResponse[Any])
async def get_top_donators():
    return await _proxy_request("GET", "/vi-tien/nguoi-ung-ho-hang-dau")

@router.get('/doanh-thu', response_model=APIResponse[Any])
async def get_revenue(current_user: UserInDB=Depends(get_current_user)):
    return await _proxy_request("GET", "/vi-tien/doanh-thu", headers={"X-User-Id": str(current_user.id)})

@router.post('/giao-dich-mua/tai-lieu/{document_id}', response_model=APIResponse[Any])
async def purchase_document(document_id: str, current_user: UserInDB=Depends(get_current_user)):
    return await _proxy_request("POST", f"/vi-tien/giao-dich-mua/tai-lieu/{document_id}", headers={"X-User-Id": str(current_user.id)})

@router.post('/giao-dich-mua/tai-lieu/{document_id}/chuong/{chapter_id}', response_model=APIResponse[Any])
async def purchase_chapter(document_id: str, chapter_id: str, current_user: UserInDB=Depends(get_current_user)):
    return await _proxy_request("POST", f"/vi-tien/giao-dich-mua/tai-lieu/{document_id}/chuong/{chapter_id}", headers={"X-User-Id": str(current_user.id)})

@router.post('/giao-dich-mua/{purchase_id}/huy-bo', response_model=APIResponse[Any])
async def cancel_purchase(purchase_id: str, current_user: UserInDB=Depends(get_current_user)):
    return await _proxy_request("POST", f"/vi-tien/giao-dich-mua/{purchase_id}/huy-bo", headers={"X-User-Id": str(current_user.id)})