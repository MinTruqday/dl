from typing import Any

from src.core.logging_route import LoggingRoute
from fastapi import APIRouter, Depends
from src.services.passkey import PasskeyService

from src.core.dependency import get_current_user
from src.core.response import APIResponse
from src.schemas.identity import PasskeyFinishRequest, PasskeyRequest

router = APIRouter(route_class=LoggingRoute, prefix="/xac-thuc/khoa-bao-mat")

@router.post("/dang-nhap/bat-dau", response_model=APIResponse[Any])
async def passkey_login_begin(payload: PasskeyRequest):
    return APIResponse(
        data=await PasskeyService.login_begin(payload.email),
        message="Bắt đầu xác thực bằng mã bảo mật thành công",
        status=200,
    )

@router.post("/dang-nhap/hoan-tat", response_model=APIResponse[Any])
async def passkey_login_finish(payload: PasskeyFinishRequest):
    return APIResponse(
        data=await PasskeyService.login_finish(
            payload.email, payload.credential
        ),
        message="Xác thực thành công",
        status=200,
    )

@router.post("/dang-ky/bat-dau", response_model=APIResponse[Any])
async def passkey_register_begin(payload: PasskeyRequest):
    return APIResponse(
        data=await PasskeyService.register_begin(payload.email),
        message="Bắt đầu đăng ký mã bảo mật thành công",
        status=200,
    )

@router.post("/dang-ky/hoan-tat", response_model=APIResponse[Any])
async def passkey_register_finish(payload: PasskeyFinishRequest):
    return APIResponse(
        data=await PasskeyService.register_finish(
            payload.email, payload.credential
        ),
        message="Đăng ký mã bảo mật thành công",
        status=200,
    )
