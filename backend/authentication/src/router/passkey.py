from typing import Any

from fastapi import APIRouter, Depends
from src.services.passkey import PasskeyManager

from core.dependency import get_current_user, get_db
from core.response import APIResponse
from core.schemas.user import PasskeyFinishRequest, PasskeyRequest

router = APIRouter(prefix="/auth/passkey")


@router.post("/dang-nhap/bat-dau", response_model=APIResponse[Any])
async def passkey_login_begin(payload: PasskeyRequest, db=Depends(get_db)):
    return APIResponse(
        data=await PasskeyManager.login_begin(payload.email, db=db),
        message="Bắt đầu xác thực bằng mã bảo mật thành công",
        status=200,
    )


@router.post("/dang-nhap/hoan-tat", response_model=APIResponse[Any])
async def passkey_login_finish(payload: PasskeyFinishRequest, db=Depends(get_db)):
    return APIResponse(
        data=await PasskeyManager.login_finish(
            payload.email, payload.credential, db=db
        ),
        message="Xác thực thành công",
        status=200,
    )
