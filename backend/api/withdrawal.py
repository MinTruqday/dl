from typing import Any
from fastapi import APIRouter, Depends, HTTPException
from api.dependency import require_role, get_current_user
from models.user import UserInDB, RoleEnum
from core.response import APIResponse
from models.withdrawal import WithdrawalRequest
import httpx

from core.config import settings
FINANCE_URL = settings.FINANCE_SERVICE_URL
router = APIRouter(prefix='/rut-tien')

async def _proxy_request(method, url, **kwargs):
    async with httpx.AsyncClient() as client:
        res = await client.request(method, f"{FINANCE_URL}{url}", **kwargs)
        if res.status_code >= 400:
            raise HTTPException(status_code=res.status_code, detail=res.json().get("detail", "Lỗi từ dịch vụ tài chính"))
        return res.json()

@router.post('', response_model=APIResponse[Any], dependencies=[Depends(require_role([RoleEnum.AUTHOR]))])
async def request_withdrawal(data: WithdrawalRequest, current_user: UserInDB=Depends(get_current_user)):
    return await _proxy_request("POST", "/rut-tien", json=data.model_dump(), headers={"X-User-Id": str(current_user.id)})

@router.get('/hang-doi', response_model=APIResponse[Any], dependencies=[Depends(require_role([RoleEnum.MODERATOR, RoleEnum.ADMIN]))])
async def get_withdrawal_queue(status: str='PENDING'):
    return await _proxy_request("GET", "/rut-tien/hang-doi", params={"status": status})

@router.post('/{withdrawal_id}/xac-thuc', response_model=APIResponse[Any], dependencies=[Depends(require_role([RoleEnum.MODERATOR, RoleEnum.ADMIN]))])
async def verify_withdrawal(withdrawal_id: str, action: str, current_user: UserInDB=Depends(get_current_user)):
    return await _proxy_request("POST", f"/rut-tien/{withdrawal_id}/xac-thuc", params={"action": action}, headers={"X-User-Id": str(current_user.id)})

@router.post('/{withdrawal_id}/huy-bo', response_model=APIResponse[Any], dependencies=[Depends(require_role([RoleEnum.AUTHOR]))])
async def cancel_withdrawal(withdrawal_id: str, current_user: UserInDB=Depends(get_current_user)):
    return await _proxy_request("POST", f"/rut-tien/{withdrawal_id}/huy-bo", headers={"X-User-Id": str(current_user.id)})

@router.get('/ca-nhan', response_model=APIResponse[Any], dependencies=[Depends(require_role([RoleEnum.AUTHOR]))])
async def get_my_withdrawals(current_user: UserInDB=Depends(get_current_user)):
    return await _proxy_request("GET", "/rut-tien/ca-nhan", headers={"X-User-Id": str(current_user.id)})