from typing import Any
from fastapi import APIRouter, Depends, HTTPException
from api.dependency import get_db
from core.response import APIResponse
from core.config import settings
from models.user import PasskeyRequest, PasskeyFinishRequest
import httpx

AUTH_URL = settings.AUTHENTICATION_SERVICE_URL
router = APIRouter(prefix='/xac-thuc/passkey')

async def _proxy(method: str, path: str, **kwargs):
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            res = await client.request(method, f"{AUTH_URL}{path}", **kwargs)
            if res.status_code >= 400:
                raise HTTPException(status_code=res.status_code, detail=res.json().get("detail", "Lỗi Passkey"))
            return res.json()
        except HTTPException:
            raise
        except httpx.RequestError as e:
            raise HTTPException(status_code=503, detail=f"Không thể kết nối đến Authentication Service: {e}")

@router.post('/dang-ky/bat-dau', response_model=APIResponse[Any])
async def passkey_register_begin(payload: PasskeyRequest):
    return await _proxy("POST", "/xac-thuc/passkey/dang-ky/bat-dau", json=payload.model_dump())

@router.post('/dang-ky/hoan-tat', response_model=APIResponse[Any])
async def passkey_register_finish(payload: PasskeyFinishRequest):
    return await _proxy("POST", "/xac-thuc/passkey/dang-ky/hoan-tat", json=payload.model_dump())

@router.post('/dang-nhap/bat-dau', response_model=APIResponse[Any])
async def passkey_login_begin(payload: PasskeyRequest):
    return await _proxy("POST", "/xac-thuc/passkey/dang-nhap/bat-dau", json=payload.model_dump())

@router.post('/dang-nhap/hoan-tat', response_model=APIResponse[Any])
async def passkey_login_finish(payload: PasskeyFinishRequest):
    return await _proxy("POST", "/xac-thuc/passkey/dang-nhap/hoan-tat", json=payload.model_dump())