from typing import Any

from core.dependency import get_current_user, get_db
from core.response import APIResponse
from core.schemas.user import PasskeyFinishRequest, PasskeyRequest
from fastapi import APIRouter, Depends
from src.services.passkey_service import PasskeyService

router = APIRouter(prefix="/auth/passkey")


@router.post("/login/start", response_model=APIResponse[Any])
async def passkey_login_begin(payload: PasskeyRequest, db=Depends(get_db)):
    return APIResponse(
        data=await PasskeyService.login_begin(payload.email, db=db),
        message="Bắt đầu quá trình đăng nhập Passkey",
        status=200,
    )


@router.post("/login/hoan-tat", response_model=APIResponse[Any])
async def passkey_login_finish(payload: PasskeyFinishRequest, db=Depends(get_db)):
    return APIResponse(
        data=await PasskeyService.login_finish(
            payload.email, payload.credential, db=db
        ),
        message="Đã đăng nhập bằng Passkey",
        status=200,
    )
