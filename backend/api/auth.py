from typing import Any
from core.response import APIResponse
from fastapi import APIRouter, Depends, status, Request
from fastapi.security import OAuth2PasswordRequestForm
from models.user import UserCreate, UserInDB, UserResponse
from api.dependency import get_current_user, RateLimiter
from services.auth import AuthService
from pydantic import BaseModel, EmailStr
from typing import Any
from services.passkey import PasskeyService

router = APIRouter(prefix="/auth")

class ForgotPasswordRequest(BaseModel):
    email: EmailStr

class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str

class VerifyCodeRequest(BaseModel):
    token: str

class PasskeyRequest(BaseModel):
    email: EmailStr

class PasskeyFinishRequest(BaseModel):
    email: EmailStr
    credential: dict

@router.get("/me", response_model=APIResponse[UserResponse])
async def read_users_me(current_user: UserInDB = Depends(get_current_user)):
    user_data = current_user.model_dump()
    user_data["has_passkey"] = len(current_user.passkeys) > 0
    return APIResponse(data=user_data, message="Lấy thông tin cá nhân thành công.", status=status.HTTP_200_OK)

@router.post("/register", response_model=APIResponse[UserResponse], status_code=status.HTTP_201_CREATED, dependencies=[Depends(RateLimiter(calls=3, period=60))])
async def register_user(user_in: UserCreate, request: Request) -> Any:
    client_ip = request.client.host if request.client else "unknown"
    return APIResponse(data=await AuthService.register_user(user_in, client_ip), message="Đăng ký tài khoản thành công.", status=status.HTTP_201_CREATED)

@router.post("/login", response_model=APIResponse[Any], dependencies=[Depends(RateLimiter(calls=5, period=60))])
async def login(request: Request, form_data: OAuth2PasswordRequestForm = Depends()) -> Any:
    client_ip = request.client.host if request.client else "unknown"
    return APIResponse(data=await AuthService.login_user(form_data.username, form_data.password, client_ip), message="Đăng nhập thành công.", status=status.HTTP_200_OK)

@router.post("/forgot-password", response_model=APIResponse[Any])
async def forgot_password(payload: ForgotPasswordRequest, request: Request) -> Any:
    client_ip = request.client.host if request.client else "unknown"
    return APIResponse(data=await AuthService.forgot_password(payload.email, client_ip), message="Yêu cầu khôi phục mật khẩu đã được gửi.", status=status.HTTP_200_OK)

@router.post("/reset-password", response_model=APIResponse[Any])
async def reset_password(payload: ResetPasswordRequest, request: Request) -> Any:
    client_ip = request.client.host if request.client else "unknown"
    return APIResponse(data=await AuthService.reset_password(payload.token, payload.new_password, client_ip), message="Đặt lại mật khẩu thành công.", status=status.HTTP_200_OK)

@router.post("/verify-code", response_model=APIResponse[Any])
async def verify_code(payload: VerifyCodeRequest, request: Request) -> Any:
    client_ip = request.client.host if request.client else "unknown"
    return APIResponse(data=await AuthService.verify_reset_code(payload.token, client_ip), message="Mã xác thực hợp lệ.", status=status.HTTP_200_OK)

@router.get("/google/login", response_model=APIResponse[Any])
async def google_login():
    auth_url = await AuthService.get_google_auth_url()
    return APIResponse(data={"url": auth_url}, message="Lấy liên kết đăng nhập Google thành công.", status=200)

@router.get("/google/callback", response_model=APIResponse[Any])
async def google_callback(code: str, request: Request):
    client_ip = request.client.host if request.client else "unknown"
    return APIResponse(data=await AuthService.handle_google_callback(code, client_ip), message="Đăng nhập Google thành công.", status=200)

@router.get("/authors/featured", response_model=APIResponse[Any])
async def get_featured_authors(limit: int = 5):
    return APIResponse(data=await AuthService.get_featured_authors(limit), message="Lấy danh sách tác giả nổi bật thành công.", status=200)

@router.post("/passkey/register/begin", response_model=APIResponse[Any])
async def passkey_register_begin(payload: PasskeyRequest):
    return APIResponse(data=await PasskeyService.register_begin(payload.email), message="Khởi tạo đăng ký Passkey thành công.", status=200)

@router.post("/passkey/register/finish", response_model=APIResponse[Any])
async def passkey_register_finish(payload: PasskeyFinishRequest):
    return APIResponse(data=await PasskeyService.register_finish(payload.email, payload.credential), message="Hoàn tất đăng ký Passkey thành công.", status=200)

@router.post("/passkey/login/begin", response_model=APIResponse[Any])
async def passkey_login_begin(payload: PasskeyRequest):
    return APIResponse(data=await PasskeyService.login_begin(payload.email), message="Khởi tạo đăng nhập Passkey thành công.", status=200)

@router.post("/passkey/login/finish", response_model=APIResponse[Any])
async def passkey_login_finish(payload: PasskeyFinishRequest):
    return APIResponse(data=await PasskeyService.login_finish(payload.email, payload.credential), message="Đăng nhập bằng Passkey thành công.", status=200)
