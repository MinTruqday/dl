from typing import Any

from fastapi import APIRouter, Depends, Request, status
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel, EmailStr
from src.services.auth import AuthManager

from core.dependency import RateLimiter, get_current_user, get_db
from core.response import APIResponse
from core.schemas.user import (
    ForgotPasswordRequest,
    ResetPasswordRequest,
    UserCreate,
    UserInDB,
    UserResponse,
    VerifyCodeRequest,
)

router = APIRouter(prefix="/xac-thuc")


@router.get("/ca-nhan", response_model=APIResponse[UserResponse])
async def read_users_me(
    current_user: UserInDB = Depends(get_current_user), db=Depends(get_db)
):
    user_data = current_user.model_dump()
    user_data["has_passkey"] = (
        len(current_user.passkeys) > 0 if current_user.passkeys else False
    )
    return APIResponse(
        data=user_data,
        message="Lấy thông tin cá nhân thành công",
        status=status.HTTP_200_OK,
    )


@router.post(
    "/register",
    response_model=APIResponse[UserResponse],
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(RateLimiter(calls=3, period=60))],
)
async def register_user(
    user_in: UserCreate, request: Request, db=Depends(get_db)
) -> Any:
    client_ip = request.client.host if request.client else "unknown"
    return APIResponse(
        data=await AuthManager.register_user(user_in, client_ip, db=db),
        message="Đăng ký thành công, vui lòng đăng nhập",
        status=status.HTTP_201_CREATED,
    )


@router.post(
    "/login",
    response_model=APIResponse[Any],
    dependencies=[Depends(RateLimiter(calls=5, period=60))],
)
async def login(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db=Depends(get_db),
) -> Any:
    client_ip = request.client.host if request.client else "unknown"
    return APIResponse(
        data=await AuthManager.login_user(
            form_data.username, form_data.password, client_ip, db=db
        ),
        message="Xác thực và cấp quyền truy cập thành công",
        status=status.HTTP_200_OK,
    )


@router.post("/quen-mat-khau", response_model=APIResponse[Any])
async def forgot_password(
    payload: ForgotPasswordRequest, request: Request, db=Depends(get_db)
) -> Any:
    client_ip = request.client.host if request.client else "unknown"
    return APIResponse(
        data=await AuthManager.forgot_password(payload.email, client_ip, db=db),
        message="Yêu cầu đặt lại mật khẩu đã được gửi đi",
        status=status.HTTP_200_OK,
    )


@router.post("/dat-lai-mat-khau", response_model=APIResponse[Any])
async def reset_password(
    payload: ResetPasswordRequest, request: Request, db=Depends(get_db)
) -> Any:
    client_ip = request.client.host if request.client else "unknown"
    return APIResponse(
        data=await AuthManager.reset_password(
            payload.token, payload.new_password, client_ip, db=db
        ),
        message="Đổi mật khẩu thành công",
        status=status.HTTP_200_OK,
    )


@router.post("/xac-nhan-ma", response_model=APIResponse[Any])
async def verify_code(
    payload: VerifyCodeRequest, request: Request, db=Depends(get_db)
) -> Any:
    client_ip = request.client.host if request.client else "unknown"
    return APIResponse(
        data=await AuthManager.verify_reset_code(payload.token, client_ip, db=db),
        message="Xác thực mã bảo mật thành công",
        status=status.HTTP_200_OK,
    )


@router.get("/google/dang-nhap", response_model=APIResponse[Any])
async def google_login(db=Depends(get_db)):
    auth_url = await AuthManager.get_google_auth_url(db=db)
    return APIResponse(
        data={"url": auth_url},
        message="Tạo liên kết cổng xác thực thành công",
        status=200,
    )


@router.get("/google/phan-hoi", response_model=APIResponse[Any])
async def google_callback(code: str, request: Request, db=Depends(get_db)):
    client_ip = request.client.host if request.client else "unknown"
    return APIResponse(
        data=await AuthManager.handle_google_callback(code, client_ip, db=db),
        message="Xác thực liên kết thành công",
        status=200,
    )
