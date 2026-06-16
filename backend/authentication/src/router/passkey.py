from typing import Any
from core.dependency import get_db
from core.response import APIResponse
from fastapi import APIRouter, Depends
from src.schemas.auth import PasskeyRequest, PasskeyFinishRequest
from src.services.passkey import PasskeyService

router = APIRouter(prefix="/auth/passkey")

@router.post("/login/start", response_model=APIResponse[Any])
async def passkey_login_begin(payload: PasskeyRequest, db=Depends(get_db)):
    return APIResponse(
        data=await PasskeyService.login_begin(payload.email, db=db),
        message="Secure passkey authentication process successfully initiated for the requested user account",
        status=200,
    )

@router.post("/login/finish", response_model=APIResponse[Any])
async def passkey_login_finish(payload: PasskeyFinishRequest, db=Depends(get_db)):
    return APIResponse(
        data=await PasskeyService.login_finish(payload.email, payload.credential, db=db),
        message="User successfully authenticated and verified using the provided secure passkey credentials",
        status=200,
    )