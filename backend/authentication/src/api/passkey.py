from typing import Any

from fastapi import APIRouter, Depends
from src.services.passkey import PasskeyService

from shared.dependency import get_current_user, get_db
from shared.response import APIResponse
from src.schemas.authentication import PasskeyFinishRequest, PasskeyRequest

router = APIRouter(prefix="/xac-thuc/khoa-bao-mat")


@router.post("/dang-nhap/bat-dau", response_model=APIResponse[Any])
async def passkey_login_begin(payload: PasskeyRequest, db=Depends(get_db)):
    return APIResponse(
        data=await PasskeyService.login_begin(payload.email, db=db),
        message="Bắt đầu xác thực bằng mã bảo mật thành công",
        status=200,
    )


@router.post("/dang-nhap/hoan-tat", response_model=APIResponse[Any])
async def passkey_login_finish(payload: PasskeyFinishRequest, db=Depends(get_db)):
    return APIResponse(
        data=await PasskeyService.login_finish(
            payload.email, payload.credential, db=db
        ),
        message="Xác thực thành công",
        status=200,
    )


@router.post("/dang-ky/bat-dau", response_model=APIResponse[Any])
async def passkey_register_begin(payload: PasskeyRequest, db=Depends(get_db)):
    return APIResponse(
        data=await PasskeyService.register_begin(payload.email, db=db),
        message="Bắt đầu đăng ký mã bảo mật thành công",
        status=200,
    )


@router.post("/dang-ky/hoan-tat", response_model=APIResponse[Any])
async def passkey_register_finish(payload: PasskeyFinishRequest, db=Depends(get_db)):
    return APIResponse(
        data=await PasskeyService.register_finish(
            payload.email, payload.credential, db=db
        ),
        message="Đăng ký mã bảo mật thành công",
        status=200,
    )
