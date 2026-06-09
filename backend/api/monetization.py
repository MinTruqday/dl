from typing import Any
from fastapi import APIRouter, Depends, HTTPException
from api.dependency import require_role, get_current_user
from models.user import UserInDB, RoleEnum
from core.response import APIResponse
from models.wallet import PlanCreate, TipRequest, DocumentPricingRequest, FlashSaleRequest
import httpx

from core.config import settings
FINANCE_URL = settings.FINANCE_SERVICE_URL
router = APIRouter(prefix='/kiem-tien')

async def _proxy_request(method, url, **kwargs):
    async with httpx.AsyncClient() as client:
        res = await client.request(method, f"{FINANCE_URL}{url}", **kwargs)
        if res.status_code >= 400:
            raise HTTPException(status_code=res.status_code, detail=res.json().get("detail", "Lỗi từ dịch vụ tài chính"))
        return res.json()

@router.post('/goi-hoi-vien', response_model=APIResponse[Any])
async def create_plan(plan: PlanCreate, current_user: UserInDB=Depends(get_current_user)):
    return await _proxy_request("POST", "/kiem-tien/goi-hoi-vien", json=plan.model_dump(), headers={"X-User-Id": str(current_user.id)})

@router.get('/goi-hoi-vien/{author_id}', response_model=APIResponse[Any])
async def get_plans(author_id: str):
    return await _proxy_request("GET", f"/kiem-tien/goi-hoi-vien/{author_id}")

@router.post('/dang-ky/{plan_id}', response_model=APIResponse[Any])
async def subscribe(plan_id: str, current_user: UserInDB=Depends(get_current_user)):
    return await _proxy_request("POST", f"/kiem-tien/dang-ky/{plan_id}", headers={"X-User-Id": str(current_user.id)})

@router.get('/danh-sach-dang-ky/ca-nhan', response_model=APIResponse[Any])
async def get_my_subscriptions(current_user: UserInDB=Depends(get_current_user)):
    return await _proxy_request("GET", "/kiem-tien/danh-sach-dang-ky/ca-nhan", headers={"X-User-Id": str(current_user.id)})

@router.post('/danh-sach-dang-ky/{subscription_id}/tam-dung', response_model=APIResponse[Any])
async def pause_subscription(subscription_id: str, current_user: UserInDB=Depends(get_current_user)):
    return await _proxy_request("POST", f"/kiem-tien/danh-sach-dang-ky/{subscription_id}/tam-dung", headers={"X-User-Id": str(current_user.id)})

@router.post('/danh-sach-dang-ky/{subscription_id}/tiep-tuc', response_model=APIResponse[Any])
async def resume_subscription(subscription_id: str, current_user: UserInDB=Depends(get_current_user)):
    return await _proxy_request("POST", f"/kiem-tien/danh-sach-dang-ky/{subscription_id}/tiep-tuc", headers={"X-User-Id": str(current_user.id)})

@router.post('/danh-sach-dang-ky/{subscription_id}/huy', response_model=APIResponse[Any])
async def cancel_subscription(subscription_id: str, current_user: UserInDB=Depends(get_current_user)):
    return await _proxy_request("POST", f"/kiem-tien/danh-sach-dang-ky/{subscription_id}/huy", headers={"X-User-Id": str(current_user.id)})

@router.post('/ung-ho', response_model=APIResponse[Any])
async def tip(req: TipRequest, current_user: UserInDB=Depends(get_current_user)):
    return await _proxy_request("POST", "/kiem-tien/ung-ho", json=req.model_dump(), headers={"X-User-Id": str(current_user.id)})

@router.put('/tai-lieu/{document_id}/gia-ban', response_model=APIResponse[Any])
async def set_document_pricing(document_id: str, data: DocumentPricingRequest, current_user: UserInDB=Depends(get_current_user)):
    return await _proxy_request("PUT", f"/kiem-tien/tai-lieu/{document_id}/gia-ban", json=data.model_dump(), headers={"X-User-Id": str(current_user.id)})

@router.post('/tai-lieu/{document_id}/flash-sale', response_model=APIResponse[Any])
async def set_flash_sale(document_id: str, data: FlashSaleRequest, current_user: UserInDB=Depends(get_current_user)):
    return await _proxy_request("POST", f"/kiem-tien/tai-lieu/{document_id}/flash-sale", json=data.model_dump(), headers={"X-User-Id": str(current_user.id)})

@router.get('/thong-ke/doanh-thu', response_model=APIResponse[Any], dependencies=[Depends(require_role([RoleEnum.AUTHOR, RoleEnum.ADMIN, RoleEnum.MODERATOR]))])
async def get_author_revenue(current_user: UserInDB=Depends(get_current_user)):
    return await _proxy_request("GET", "/kiem-tien/thong-ke/doanh-thu", headers={"X-User-Id": str(current_user.id)})