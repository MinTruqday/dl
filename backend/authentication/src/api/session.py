from src.core.infrastructure.mongo import mongo
from src.core.dependency import CurrentUser
from typing import Any

from src.core.logging_route import LoggingRoute
from fastapi import APIRouter, Depends, Request, status
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel, EmailStr
from src.services.session import SessionService

from src.core.dependency import RateLimiting, get_current_user
from src.core.response import APIResponse
from src.schemas.identity import (
    ForgotPasswordRequest,
    ResetPasswordRequest,
    UserCreate,
    UserInDB,
    UserResponse,
    VerifyCodeRequest,
)

router = APIRouter(route_class=LoggingRoute, prefix="/xac-thuc")

@router.get("/ca-nhan", response_model=APIResponse[UserResponse])
async def read_users_me(
    current_user: CurrentUser = Depends(get_current_user)
):
    user_doc = await mongo.find_one(collection="users", query={"_id": current_user.id})
    if not user_doc:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Không tìm thấy người dùng")
        
    user_data = user_doc
    user_data["_id"] = str(user_doc["_id"])
    if "created_at" not in user_data:
        from datetime import datetime, timezone
        user_data["created_at"] = datetime.now(timezone.utc)
    passkeys = user_doc.get("passkeys", [])
    user_data["has_passkey"] = len(passkeys) > 0
    
    return APIResponse(
        data=user_data,
        message="Lấy thông tin cá nhân thành công",
        status=status.HTTP_200_OK,
    )

@router.post(
    "/dang-ky",
    response_model=APIResponse[UserResponse],
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(RateLimiting(calls=3, period=60))],
)
async def register_user(
    user_in: UserCreate, request: Request
) -> Any:
    client_ip = request.client.host if request.client else "unknown"
    return APIResponse(
        data=await SessionService.register_user(user_in, client_ip),
        message="Đăng ký thành công, vui lòng đăng nhập",
        status=status.HTTP_201_CREATED,
    )

@router.post(
    "/dang-nhap",
    response_model=APIResponse[Any],
    dependencies=[Depends(RateLimiting(calls=5, period=60))],
)
async def login(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
) -> Any:
    client_ip = request.client.host if request.client else "unknown"
    return APIResponse(
        data=await SessionService.login_user(
            form_data.username, form_data.password, client_ip
        ),
        message="Xác thực và cấp quyền truy cập thành công",
        status=status.HTTP_200_OK,
    )

@router.post("/quen-mat-khau", response_model=APIResponse[Any])
async def forgot_password(
    payload: ForgotPasswordRequest, request: Request
) -> Any:
    client_ip = request.client.host if request.client else "unknown"
    return APIResponse(
        data=await SessionService.forgot_password(payload.email, client_ip),
        message="Yêu cầu đặt lại mật khẩu đã được gửi đi",
        status=status.HTTP_200_OK,
    )

@router.post("/dat-lai-mat-khau", response_model=APIResponse[Any])
async def reset_password(
    payload: ResetPasswordRequest, request: Request
) -> Any:
    client_ip = request.client.host if request.client else "unknown"
    return APIResponse(
        data=await SessionService.reset_password(
            payload.token, payload.new_password, client_ip
        ),
        message="Đổi mật khẩu thành công",
        status=status.HTTP_200_OK,
    )

@router.post("/xac-nhan-ma", response_model=APIResponse[Any])
async def verify_code(
    payload: VerifyCodeRequest, request: Request
) -> Any:
    client_ip = request.client.host if request.client else "unknown"
    return APIResponse(
        data=await SessionService.verify_reset_code(payload.token, client_ip),
        message="Xác thực mã bảo mật thành công",
        status=status.HTTP_200_OK,
    )

