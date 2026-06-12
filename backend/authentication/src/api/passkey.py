from fastapi import APIRouter, Depends
from src.api.dependency import get_db, get_current_user
from core.response import APIResponse
from src.schemas.user import PasskeyRequest, PasskeyFinishRequest
from src.services.passkey import PasskeyService
from typing import Any
router = APIRouter(prefix='/xac-thuc/passkey')

@router.post('/dang-nhap/bat-dau', response_model=APIResponse[Any])
async def passkey_login_begin(payload: PasskeyRequest, db=Depends(get_db)):
    return APIResponse(data=await PasskeyService.login_begin(payload.email, db=db), message='Bắt đầu quá trình đăng nhập Passkey', status=200)

@router.post('/dang-nhap/hoan-tat', response_model=APIResponse[Any])
async def passkey_login_finish(payload: PasskeyFinishRequest, db=Depends(get_db)):
    return APIResponse(data=await PasskeyService.login_finish(payload.email, payload.credential, db=db), message='Đã đăng nhập bằng Passkey', status=200)
