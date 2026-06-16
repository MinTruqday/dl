from typing import Any
from core.dependency import get_db
from core.response import APIResponse
from fastapi import APIRouter, Depends
from src.schemas.auth import PasskeyRequest, PasskeyFinishRequest
from src.services.passkey import PasskeyService

router = APIRouter(prefix="/xac-thuc/khoa-lai-xac-thuc")

@router.post("/dang-nhap-lieu/bat-dau", response_model=APIResponse[Any])
async def passkey_login_begin(payload: PasskeyRequest, db=Depends(get_db)):
    return APIResponse(
        data=await PasskeyService.login_begin(payload.email, db=db),
        message="Yêu cầu của bạn đã được hệ thống tiếp nhận và xử lý thành công",
        status=200,
    )

@router.post("/dang-nhap-lieu/hoan-thanh", response_model=APIResponse[Any])
async def passkey_login_finish(payload: PasskeyFinishRequest, db=Depends(get_db)):
    return APIResponse(
        data=await PasskeyService.login_finish(payload.email, payload.credential, db=db),
        message="Yêu cầu của bạn đã được hệ thống tiếp nhận và xử lý thành công",
        status=200,
    )