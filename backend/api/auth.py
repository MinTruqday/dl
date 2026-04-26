from fastapi import APIRouter, Depends, status, Request
from fastapi.security import OAuth2PasswordRequestForm
from models.user import UserCreate, UserInDB, UserResponse
from api.dependencies import get_current_user, RateLimiter
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

class PasskeyRequest(BaseModel):
    email: EmailStr

class PasskeyFinishRequest(BaseModel):
    email: EmailStr
    credential: dict

@router.get("/me", response_model=UserResponse)
async def read_users_me(current_user: UserInDB = Depends(get_current_user)):
    return current_user

@router.post("/register", response_model=UserResponse, dependencies=[Depends(RateLimiter(calls=3, period=60))])
async def register_user(user_in: UserCreate, request: Request) -> Any:
    client_ip = request.client.host if request.client else "unknown"
    return await AuthService.register_user(user_in, client_ip)

@router.post("/login", dependencies=[Depends(RateLimiter(calls=5, period=60))])
async def login(request: Request, form_data: OAuth2PasswordRequestForm = Depends()) -> Any:
    client_ip = request.client.host if request.client else "unknown"
    return await AuthService.login_user(form_data.username, form_data.password, client_ip)

@router.post("/forgot-password")
async def forgot_password(payload: ForgotPasswordRequest, request: Request) -> Any:
    client_ip = request.client.host if request.client else "unknown"
    return await AuthService.forgot_password(payload.email, client_ip)

@router.post("/reset-password")
async def reset_password(payload: ResetPasswordRequest, request: Request) -> Any:
    client_ip = request.client.host if request.client else "unknown"
    return await AuthService.reset_password(payload.token, payload.new_password, client_ip)

@router.get("/google/login")
async def google_login():
    auth_url = await AuthService.get_google_auth_url()
    return {"url": auth_url}

@router.get("/google/callback")
async def google_callback(code: str, request: Request):
    client_ip = request.client.host if request.client else "unknown"
    return await AuthService.handle_google_callback(code, client_ip)
@router.get("/authors/featured")
async def get_featured_authors(limit: int = 5):
    return await AuthService.get_featured_authors(limit)

@router.post("/passkey/register/begin")
async def passkey_register_begin(payload: PasskeyRequest):
    return await PasskeyService.register_begin(payload.email)

@router.post("/passkey/register/finish")
async def passkey_register_finish(payload: PasskeyFinishRequest):
    return await PasskeyService.register_finish(payload.email, payload.credential)

@router.post("/passkey/login/begin")
async def passkey_login_begin(payload: PasskeyRequest):
    return await PasskeyService.login_begin(payload.email)

@router.post("/passkey/login/finish")
async def passkey_login_finish(payload: PasskeyFinishRequest):
    return await PasskeyService.login_finish(payload.email, payload.credential)
