from typing import Any, Optional
from fastapi import APIRouter, Depends, HTTPException
from api.dependency import require_role, get_current_user
from models.user import UserInDB, RoleEnum
from core.response import APIResponse
from models.wallet import CouponCreateRequest
import httpx

from core.config import settings
FINANCE_URL = settings.FINANCE_SERVICE_URL
router = APIRouter(prefix='/ma-uu-dai')

async def _proxy_request(method, url, **kwargs):
    async with httpx.AsyncClient() as client:
        res = await client.request(method, f"{FINANCE_URL}{url}", **kwargs)
        if res.status_code >= 400:
            raise HTTPException(status_code=res.status_code, detail=res.json().get("detail", "Lỗi từ dịch vụ tài chính"))
        return res.json()

@router.get('/kiem-tra', response_model=APIResponse[Any])
async def validate_coupon(code: str, document_id: Optional[str]=None, current_user: UserInDB=Depends(get_current_user)):
    params = {"code": code}
    if document_id:
        params["document_id"] = document_id
    return await _proxy_request("GET", "/ma-uu-dai/kiem-tra", params=params, headers={"X-User-Id": str(current_user.id)})

@router.get('', response_model=APIResponse[Any])
async def get_coupons(current_user: UserInDB=Depends(require_role([RoleEnum.AUTHOR, RoleEnum.ADMIN]))):
    return await _proxy_request("GET", "/ma-uu-dai", headers={"X-User-Id": str(current_user.id)})

@router.post('', response_model=APIResponse[Any])
async def create_coupon(data: CouponCreateRequest, current_user: UserInDB=Depends(require_role([RoleEnum.AUTHOR, RoleEnum.ADMIN]))):
    return await _proxy_request("POST", "/ma-uu-dai", json=data.model_dump(), headers={"X-User-Id": str(current_user.id)})

@router.post('/{coupon_id}/phe-duyet', response_model=APIResponse[Any])
async def approve_coupon(coupon_id: str, action: str='approve', current_user: UserInDB=Depends(require_role([RoleEnum.ADMIN]))):
    return await _proxy_request("POST", f"/ma-uu-dai/{coupon_id}/phe-duyet", params={"action": action}, headers={"X-User-Id": str(current_user.id)})

@router.patch('/{coupon_id}/trang-thai', response_model=APIResponse[Any])
async def toggle_coupon_status(coupon_id: str, current_user: UserInDB=Depends(require_role([RoleEnum.AUTHOR, RoleEnum.ADMIN]))):
    return await _proxy_request("PATCH", f"/ma-uu-dai/{coupon_id}/trang-thai", headers={"X-User-Id": str(current_user.id)})

@router.delete('/{coupon_id}', response_model=APIResponse[Any])
async def delete_coupon(coupon_id: str, current_user: UserInDB=Depends(require_role([RoleEnum.AUTHOR, RoleEnum.ADMIN]))):
    return await _proxy_request("DELETE", f"/ma-uu-dai/{coupon_id}", headers={"X-User-Id": str(current_user.id)})