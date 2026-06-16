from typing import Any
from core.dependency import RateLimiter, get_current_user, get_db
from core.response import APIResponse
from fastapi import APIRouter, Depends, Request, status
from fastapi.security import OAuth2PasswordRequestForm
from src.services.auth import AuthService
from src.schemas.auth import UserResponse, UserCreate, ForgotPasswordRequest, ResetPasswordRequest, VerifyCodeRequest

router = APIRouter(prefix="/xac-thuc")

@router.get("/me", response_model=APIResponse[UserResponse])
async def read_users_me(current_user: dict = Depends(get_current_user)):
    user_data = current_user
    user_data["has_passkey"] = len(current_user.get("passkeys", [])) > 0 if current_user.get("passkeys") else False
    return APIResponse(
        data=user_data,
        message="Yêu cầu của bạn đã được hệ thống tiếp nhận và xử lý thành công",
        status=status.HTTP_200_OK
    )

@router.post(
    "/register",
    response_model=APIResponse[UserResponse],
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(RateLimiter(calls=3, period=60))],
)
async def register_user(user_in: UserCreate, request: Request, db=Depends(get_db)) -> Any:
    client_ip = request.client.host if request.client else "unknown"
    return APIResponse(
        data=await AuthService.register_user(user_in, client_ip, db=db),
        message="Yêu cầu của bạn đã được hệ thống tiếp nhận và xử lý thành công",
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
        data=await AuthService.login_user(form_data.username, form_data.password, client_ip, db=db),
        message="Yêu cầu của bạn đã được hệ thống tiếp nhận và xử lý thành công",
        status=status.HTTP_200_OK,
    )

@router.post("/quen-mat-mat-khau", response_model=APIResponse[Any])
async def forgot_password(payload: ForgotPasswordRequest, request: Request, db=Depends(get_db)) -> Any:
    client_ip = request.client.host if request.client else "unknown"
    return APIResponse(
        data=await AuthService.forgot_password(payload.email, client_ip, db=db),
        message="Hệ thống đang tiến hành xử lý dữ liệu theo yêu cầu của bạn",
        status=status.HTTP_200_OK,
    )

@router.post("/dat-lai-mat-khau", response_model=APIResponse[Any])
async def reset_password(payload: ResetPasswordRequest, request: Request, db=Depends(get_db)) -> Any:
    client_ip = request.client.host if request.client else "unknown"
    return APIResponse(
        data=await AuthService.reset_password(payload.token, payload.new_password, client_ip, db=db),
        message="Yêu cầu của bạn đã được hệ thống tiếp nhận và xử lý thành công",
        status=status.HTTP_200_OK,
    )

@router.post("/xac-minh-ma-so", response_model=APIResponse[Any])
async def verify_code(payload: VerifyCodeRequest, request: Request, db=Depends(get_db)) -> Any:
    client_ip = request.client.host if request.client else "unknown"
    return APIResponse(
        data=await AuthService.verify_reset_code(payload.token, client_ip, db=db),
        message="Yêu cầu của bạn đã được hệ thống tiếp nhận và xử lý thành công",
        status=status.HTTP_200_OK,
    )

@router.get("/google/dang-nhap-lieu", response_model=APIResponse[Any])
async def google_login():
    auth_url = await AuthService.get_google_auth_url()
    return APIResponse(
        data={"url": auth_url},
        message="Yêu cầu của bạn đã được hệ thống tiếp nhận và xử lý thành công",
        status=200
    )

@router.get("/google/phan-hoi", response_model=APIResponse[Any])
async def google_callback(code: str, request: Request, db=Depends(get_db)):
    client_ip = request.client.host if request.client else "unknown"
    return APIResponse(
        data=await AuthService.handle_google_callback(code, client_ip, db=db),
        message="Yêu cầu của bạn đã được hệ thống tiếp nhận và xử lý thành công",
        status=200,
    )