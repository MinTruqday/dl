from typing import Any
from core.dependency import RateLimiter, get_current_user, get_db
from core.response import APIResponse
from fastapi import APIRouter, Depends, Request, status
from fastapi.security import OAuth2PasswordRequestForm
from src.services.auth import AuthService
from src.schemas.auth import UserResponse, UserCreate, ForgotPasswordRequest, ResetPasswordRequest, VerifyCodeRequest

router = APIRouter(prefix="/auth")

@router.get("/me", response_model=APIResponse[UserResponse])
async def read_users_me(current_user: dict = Depends(get_current_user)):
    user_data = current_user.model_dump()
    user_data["has_passkey"] = len(current_user.passkeys) > 0 if current_user.passkeys else False
    return APIResponse(
        data=user_data,
        message="Requested personal profile information successfully retrieved from the system records",
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
        message="Account registered successfully please proceed to login gateway to access your dashboard",
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
        message="User authentication process completed successfully and system access has been granted",
        status=status.HTTP_200_OK,
    )

@router.post("/forgot-password", response_model=APIResponse[Any])
async def forgot_password(payload: ForgotPasswordRequest, request: Request, db=Depends(get_db)) -> Any:
    client_ip = request.client.host if request.client else "unknown"
    return APIResponse(
        data=await AuthService.forgot_password(payload.email, client_ip, db=db),
        message="Password reset request initiated and instructions are being sent to registered address",
        status=status.HTTP_200_OK,
    )

@router.post("/reset-password", response_model=APIResponse[Any])
async def reset_password(payload: ResetPasswordRequest, request: Request, db=Depends(get_db)) -> Any:
    client_ip = request.client.host if request.client else "unknown"
    return APIResponse(
        data=await AuthService.reset_password(payload.token, payload.new_password, client_ip, db=db),
        message="Account password has been successfully updated and secured within the system",
        status=status.HTTP_200_OK,
    )

@router.post("/verify-code", response_model=APIResponse[Any])
async def verify_code(payload: VerifyCodeRequest, request: Request, db=Depends(get_db)) -> Any:
    client_ip = request.client.host if request.client else "unknown"
    return APIResponse(
        data=await AuthService.verify_reset_code(payload.token, client_ip, db=db),
        message="Provided verification code has been successfully validated by the authentication system",
        status=status.HTTP_200_OK,
    )

@router.get("/google/login", response_model=APIResponse[Any])
async def google_login():
    auth_url = await AuthService.get_google_auth_url()
    return APIResponse(
        data={"url": auth_url},
        message="Secure authentication gateway link for external provider has been successfully generated",
        status=200
    )

@router.get("/google/callback", response_model=APIResponse[Any])
async def google_callback(code: str, request: Request, db=Depends(get_db)):
    client_ip = request.client.host if request.client else "unknown"
    return APIResponse(
        data=await AuthService.handle_google_callback(code, client_ip, db=db),
        message="External authentication process completed successfully and system access has been granted",
        status=200,
    )