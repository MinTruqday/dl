from fastapi import APIRouter, Depends, Request, status
from typing import Any
from src.core.dependency import get_db
from src.core.response import APIResponse
from src.services.google import GoogleService

router = APIRouter(prefix="/google")

@router.get("/dang-nhap", response_model=APIResponse[Any])
async def google_login(db=Depends(get_db)):
    auth_url = await GoogleService.get_google_auth_url(db=db)
    return APIResponse(
        data={"url": auth_url},
        message="Tạo liên kết cổng xác thực thành công",
        status=200,
    )

@router.get("/callback", response_model=APIResponse[Any])
async def google_callback(code: str, request: Request, db=Depends(get_db)):
    client_ip = request.client.host if request.client else "unknown"
    return APIResponse(
        data=await GoogleService.handle_google_callback(code, client_ip, db=db),
        message="Xác thực liên kết thành công",
        status=200,
    )
