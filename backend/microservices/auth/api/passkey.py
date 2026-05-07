from fastapi import APIRouter, Depends
from api.dependency import get_current_user
from shared.core.response import APIResponse
from pydantic import BaseModel, EmailStr
from services.passkey import PasskeyService
from typing import Any
router = APIRouter(prefix="/xac-thuc/passkey")
class PasskeyRequest(BaseModel):
    email: EmailStr
class PasskeyFinishRequest(BaseModel):
    email: EmailStr
    credential: dict
@router.post("/dang-ky/bat-dau", response_model=APIResponse[Any])
async def passkey_register_begin(payload: PasskeyRequest):
    return APIResponse(data=await PasskeyService.register_begin(payload.email), message="Khởi tạo đăng ký Passkey thành công", status=200)
@router.post("/dang-ky/hoan-tat", response_model=APIResponse[Any])
async def passkey_register_finish(payload: PasskeyFinishRequest):
    return APIResponse(data=await PasskeyService.register_finish(payload.email, payload.credential), message="Hoàn tất đăng ký Passkey thành công", status=200)
@router.post("/dang-nhap/bat-dau", response_model=APIResponse[Any])
async def passkey_login_begin(payload: PasskeyRequest):
    return APIResponse(data=await PasskeyService.login_begin(payload.email), message="Khởi tạo đăng nhập Passkey thành công", status=200)
@router.post("/dang-nhap/hoan-tat", response_model=APIResponse[Any])
async def passkey_login_finish(payload: PasskeyFinishRequest):
    return APIResponse(data=await PasskeyService.login_finish(payload.email, payload.credential), message="Đăng nhập bằng Passkey thành công", status=200)
