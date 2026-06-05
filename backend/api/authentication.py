from api.dependency import get_db
from typing import Any
from core.response import APIResponse
from fastapi import APIRouter, Depends, status, Request
from fastapi.security import OAuth2PasswordRequestForm
from models.user import UserCreate, UserInDB, UserResponse, ForgotPasswordRequest, ResetPasswordRequest, VerifyCodeRequest
from api.dependency import get_current_user, RateLimiter, get_db
from services.authentication import AuthenticationService
from pydantic import BaseModel, EmailStr
from typing import Any
from services.passkey import PasskeyService
router = APIRouter(prefix='/xac-thuc')

@router.get('/ca-nhan', response_model=APIResponse[UserResponse])
async def read_users_me(current_user: UserInDB=Depends(get_current_user), db=Depends(get_db)):
    user_data = current_user.model_dump()
    user_data['has_passkey'] = len(current_user.passkeys) > 0 if current_user.passkeys else False
    return APIResponse(data=user_data, message='Lấy thông tin cá nhân thành công', status=status.HTTP_200_OK)

@router.post('/dang-ky', response_model=APIResponse[UserResponse], status_code=status.HTTP_201_CREATED, dependencies=[Depends(RateLimiter(calls=3, period=60))])
async def register_user(user_in: UserCreate, request: Request, db=Depends(get_db)) -> Any:
    client_ip = request.client.host if request.client else 'unknown'
    return APIResponse(data=await AuthenticationService.register_user(user_in, client_ip, db=db), message='Đăng ký tài khoản thành công', status=status.HTTP_201_CREATED)

@router.post('/dang-nhap', response_model=APIResponse[Any], dependencies=[Depends(RateLimiter(calls=5, period=60))])
async def login(request: Request, form_data: OAuth2PasswordRequestForm=Depends(), db=Depends(get_db)) -> Any:
    client_ip = request.client.host if request.client else 'unknown'
    return APIResponse(data=await AuthenticationService.login_user(form_data.username, form_data.password, client_ip, db=db), message='Đăng nhập thành công', status=status.HTTP_200_OK)

@router.post('/quen-mat-khau', response_model=APIResponse[Any])
async def forgot_password(payload: ForgotPasswordRequest, request: Request, db=Depends(get_db)) -> Any:
    client_ip = request.client.host if request.client else 'unknown'
    return APIResponse(data=await AuthenticationService.forgot_password(payload.email, client_ip, db=db), message='Yêu cầu khôi phục mật khẩu đã được gửi', status=status.HTTP_200_OK)

@router.post('/dat-lai-mat-khau', response_model=APIResponse[Any])
async def reset_password(payload: ResetPasswordRequest, request: Request, db=Depends(get_db)) -> Any:
    client_ip = request.client.host if request.client else 'unknown'
    return APIResponse(data=await AuthenticationService.reset_password(payload.token, payload.new_password, client_ip, db=db), message='Đặt lại mật khẩu thành công', status=status.HTTP_200_OK)

@router.post('/ma-xac-thuc', response_model=APIResponse[Any])
async def verify_code(payload: VerifyCodeRequest, request: Request, db=Depends(get_db)) -> Any:
    client_ip = request.client.host if request.client else 'unknown'
    return APIResponse(data=await AuthenticationService.verify_reset_code(payload.token, client_ip, db=db), message='Mã xác thực hợp lệ', status=status.HTTP_200_OK)

@router.get('/google/dang-nhap', response_model=APIResponse[Any])
async def google_login(db=Depends(get_db)):
    auth_url = await AuthenticationService.get_google_auth_url(db=db)
    return APIResponse(data={'url': auth_url}, message='Lấy liên kết đăng nhập Google thành công', status=200)

@router.get('/google/phan-hoi', response_model=APIResponse[Any])
async def google_callback(code: str, request: Request, db=Depends(get_db)):
    client_ip = request.client.host if request.client else 'unknown'
    return APIResponse(data=await AuthenticationService.handle_google_callback(code, client_ip, db=db), message='Đăng nhập Google thành công', status=200)