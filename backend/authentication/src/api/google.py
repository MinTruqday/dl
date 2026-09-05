from fastapi import APIRouter, Request, Response
from typing import Any
from src.api.cookies import set_refresh_cookie
from src.core.response import APIResponse
from src.services.google import GoogleService

router = APIRouter(prefix="/xac-thuc/google", tags=["Xác thực Google"])


@router.get("/dang-nhap", response_model=APIResponse[Any])
async def google_login():
    auth_url = await GoogleService.get_google_auth_url()
    return APIResponse(
        data={"url": auth_url}, message="Khởi tạo liên kết cổng xác thực hoàn tất", status=200
    )


@router.get("/chuyen-huong", response_model=APIResponse[Any])
async def google_callback(code: str, state: str, request: Request, response: Response):
    client_ip = request.client.host if request.client else "unknown"
    token_data = await GoogleService.handle_google_callback(code, state, client_ip)
    return APIResponse(
        data=set_refresh_cookie(response, request, token_data),
        message="Xác thực tài khoản thông qua liên kết ngoài hoàn tất",
        status=200,
    )
