from typing import Any
from core.response import APIResponse
from fastapi import APIRouter, Depends, status, Request, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from api.dependency import get_current_user, RateLimiter
from core.config import settings
from models.user import UserCreate, UserInDB, ForgotPasswordRequest, ResetPasswordRequest, VerifyCodeRequest
import httpx

AUTH_URL = settings.AUTHENTICATION_SERVICE_URL
router = APIRouter(prefix='/xac-thuc')

async def _proxy(method: str, path: str, **kwargs):
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            res = await client.request(method, f"{AUTH_URL}{path}", **kwargs)
            if res.status_code >= 400:
                raise HTTPException(status_code=res.status_code, detail=res.json().get("detail", "Lỗi xác thực"))
            return res.json()
        except HTTPException:
            raise
        except httpx.RequestError as e:
            raise HTTPException(status_code=503, detail=f"Không thể kết nối đến Authentication Service: {e}")

@router.get('/ca-nhan', response_model=APIResponse[Any])
async def read_users_me(current_user: UserInDB = Depends(get_current_user)):
    return await _proxy("GET", "/xac-thuc/ca-nhan", headers={"X-User-Id": str(current_user.id)})

@router.post('/dang-ky', response_model=APIResponse[Any], status_code=status.HTTP_201_CREATED, dependencies=[Depends(RateLimiter(calls=3, period=60))])
async def register_user(user_in: UserCreate, request: Request):
    return await _proxy("POST", "/xac-thuc/dang-ky", json=user_in.model_dump(), headers={"X-Forwarded-For": request.client.host if request.client else "unknown"})

@router.post('/dang-nhap', response_model=APIResponse[Any], dependencies=[Depends(RateLimiter(calls=5, period=60))])
async def login(request: Request, form_data: OAuth2PasswordRequestForm = Depends()):
    return await _proxy("POST", "/xac-thuc/dang-nhap",
        data={"username": form_data.username, "password": form_data.password},
        headers={"Content-Type": "application/x-www-form-urlencoded", "X-Forwarded-For": request.client.host if request.client else "unknown"})

@router.post('/dang-xuat-tat-ca', response_model=APIResponse[Any])
async def revoke_all_sessions(current_user: UserInDB = Depends(get_current_user)):
    return await _proxy("POST", "/xac-thuc/dang-xuat-tat-ca", headers={"X-User-Id": str(current_user.id)})

@router.post('/quen-mat-khau', response_model=APIResponse[Any])
async def forgot_password(payload: ForgotPasswordRequest, request: Request):
    return await _proxy("POST", "/xac-thuc/quen-mat-khau",
        json=payload.model_dump(),
        headers={"X-Forwarded-For": request.client.host if request.client else "unknown"})

@router.post('/dat-lai-mat-khau', response_model=APIResponse[Any])
async def reset_password(payload: ResetPasswordRequest, request: Request):
    return await _proxy("POST", "/xac-thuc/dat-lai-mat-khau",
        json=payload.model_dump(),
        headers={"X-Forwarded-For": request.client.host if request.client else "unknown"})

@router.post('/ma-xac-thuc', response_model=APIResponse[Any])
async def verify_code(payload: VerifyCodeRequest, request: Request):
    return await _proxy("POST", "/xac-thuc/ma-xac-thuc",
        json=payload.model_dump(),
        headers={"X-Forwarded-For": request.client.host if request.client else "unknown"})

@router.get('/google/dang-nhap', response_model=APIResponse[Any])
async def google_login():
    return await _proxy("GET", "/xac-thuc/google/dang-nhap")

@router.get('/google/phan-hoi', response_model=APIResponse[Any])
async def google_callback(code: str, request: Request):
    return await _proxy("GET", "/xac-thuc/google/phan-hoi",
        params={"code": code},
        headers={"X-Forwarded-For": request.client.host if request.client else "unknown"})