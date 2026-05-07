from typing import Any
from shared.core.response import APIResponse
from fastapi import APIRouter, Depends, status, Request
from fastapi.security import OAuth2PasswordRequestForm
from shared.models.user import UserCreate, UserInDB, UserResponse
from api.dependency import get_current_user, RateLimiter
from services.authentication import AuthenticationService
from pydantic import BaseModel, EmailStr
from typing import Any
from services.passkey import PasskeyService
router = APIRouter(prefix="/xac-thuc")
class ForgotPasswordRequest(BaseModel):
    email: EmailStr
class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str
class VerifyCodeRequest(BaseModel):
    token: str
@router.get("/ca-nhan", response_model=APIResponse[UserResponse])
async def read_users_me(current_user: UserInDB = Depends(get_current_user)):
    user_data = current_user.model_dump()
    user_data["has_passkey"] = len(current_user.passkeys) > 0
    return APIResponse(data=user_data, message="Lấy thông tin cá nhân thành công", status=status.HTTP_200_OK)
@router.post("/dang-ky", response_model=APIResponse[UserResponse], status_code=status.HTTP_201_CREATED, dependencies=[Depends(RateLimiter(calls=3, period=60))])
async def register_user(user_in: UserCreate, request: Request) -> Any:
    client_ip = request.client.host if request.client else "unknown"
    return APIResponse(data=await AuthenticationService.register_user(user_in, client_ip), message="Đăng ký tài khoản thành công", status=status.HTTP_201_CREATED)
@router.post("/dang-nhap", response_model=APIResponse[Any], dependencies=[Depends(RateLimiter(calls=5, period=60))])
async def login(request: Request, form_data: OAuth2PasswordRequestForm = Depends()) -> Any:
    client_ip = request.client.host if request.client else "unknown"
    return APIResponse(data=await AuthenticationService.login_user(form_data.username, form_data.password, client_ip), message="Đăng nhập thành công", status=status.HTTP_200_OK)
@router.post("/quen-mat-khau", response_model=APIResponse[Any])
async def forgot_password(payload: ForgotPasswordRequest, request: Request) -> Any:
    client_ip = request.client.host if request.client else "unknown"
    return APIResponse(data=await AuthenticationService.forgot_password(payload.email, client_ip), message="Yêu cầu khôi phục mật khẩu đã được gửi", status=status.HTTP_200_OK)
@router.post("/dat-lai-mat-khau", response_model=APIResponse[Any])
async def reset_password(payload: ResetPasswordRequest, request: Request) -> Any:
    client_ip = request.client.host if request.client else "unknown"
    return APIResponse(data=await AuthenticationService.reset_password(payload.token, payload.new_password, client_ip), message="Đặt lại mật khẩu thành công", status=status.HTTP_200_OK)
@router.post("/ma-xac-thuc", response_model=APIResponse[Any])
async def verify_code(payload: VerifyCodeRequest, request: Request) -> Any:
    client_ip = request.client.host if request.client else "unknown"
    return APIResponse(data=await AuthenticationService.verify_reset_code(payload.token, client_ip), message="Mã xác thực hợp lệ", status=status.HTTP_200_OK)
@router.get("/google/dang-nhap", response_model=APIResponse[Any])
async def google_login():
    auth_url = await AuthenticationService.get_google_auth_url()
    return APIResponse(data={"url": auth_url}, message="Lấy liên kết đăng nhập Google thành công", status=200)
@router.get("/google/phan-hoi", response_model=APIResponse[Any])
async def google_callback(code: str, request: Request):
    client_ip = request.client.host if request.client else "unknown"
    return APIResponse(data=await AuthenticationService.handle_google_callback(code, client_ip), message="Đăng nhập Google thành công", status=200)
