from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Cookie, Depends, HTTPException, Request, Response, status
from fastapi.security import OAuth2PasswordRequestForm
from src.api.cookies import set_refresh_cookie
from src.services.session import SessionService

from src.core.dependency import CurrentUser, RateLimiting, get_current_user
from src.core.response import APIResponse
from src.schemas.identity import (
    ForgotPasswordRequest,
    ResetPasswordRequest,
    UserCreate,
    UserResponse,
    VerifyCodeRequest,
)

router = APIRouter(prefix="/xac-thuc")

@router.get("/ca-nhan", response_model=APIResponse[UserResponse])
async def read_users_me(
    current_user: CurrentUser = Depends(get_current_user)
):
    from src.repositories.identity import IdentityRepository
    user_doc = await IdentityRepository.get_auth_credential_by_id(str(current_user.id))
    if not user_doc:
        raise HTTPException(status_code=404, detail="Không tìm thấy thông tin tài khoản người dùng")

    user_data = dict(user_doc)
    user_data["_id"] = str(user_doc["_id"])
    user_data.pop("password_hash", None)
    passkeys = user_doc.get("passkeys", [])
    user_data.pop("passkeys", None)
    user_data.update(
        {
            "email": user_doc.get("email", current_user.email),
            "full_name": user_doc.get("full_name") or current_user.full_name or "Người dùng DocLib",
            "slug": user_doc.get("slug") or str(user_doc.get("email", current_user.email)).split("@", 1)[0],
            "role": user_doc.get("role", "reader"),
            "permissions": user_doc.get("permissions") or [],
            "created_at": user_doc.get("created_at") or datetime.now(timezone.utc),
            "has_passkey": len(passkeys) > 0,
        }
    )
    
    return APIResponse(
        data=user_data,
        message="Trích xuất thông tin cá nhân hoàn tất",
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
        message="Đăng ký tài khoản hoàn tất, vui lòng tiến hành đăng nhập",
        status=status.HTTP_201_CREATED,
    )

@router.post(
    "/dang-nhap",
    response_model=APIResponse[Any],
    dependencies=[Depends(RateLimiting(calls=5, period=60))],
)
async def login(
    request: Request,
    response: Response,
    form_data: OAuth2PasswordRequestForm = Depends(),
) -> Any:
    client_ip = request.client.host if request.client else "unknown"
    token_data = await SessionService.login_user(
        form_data.username, form_data.password, client_ip
    )
    return APIResponse(
        data=set_refresh_cookie(response, request, token_data),
        message="Xác thực thông tin và cấp quyền truy cập hệ thống hoàn tất",
        status=status.HTTP_200_OK,
    )

@router.post(
    "/quen-mat-khau",
    response_model=APIResponse[Any],
    dependencies=[Depends(RateLimiting(calls=3, period=300))],
)
async def forgot_password(
    payload: ForgotPasswordRequest, request: Request
) -> Any:
    client_ip = request.client.host if request.client else "unknown"
    return APIResponse(
        data=await SessionService.forgot_password(payload.email, client_ip),
        message="Thực hiện truyền tải yêu cầu đặt lại mật khẩu hoàn tất",
        status=status.HTTP_200_OK,
    )

@router.post(
    "/dat-lai-mat-khau",
    response_model=APIResponse[Any],
    dependencies=[Depends(RateLimiting(calls=5, period=300))],
)
async def reset_password(
    payload: ResetPasswordRequest, request: Request
) -> Any:
    client_ip = request.client.host if request.client else "unknown"
    return APIResponse(
        data=await SessionService.reset_password(
            payload.token, payload.new_password, client_ip
        ),
        message="Thực hiện thay đổi mật khẩu tài khoản hoàn tất",
        status=status.HTTP_200_OK,
    )

@router.post(
    "/xac-nhan-ma",
    response_model=APIResponse[Any],
    dependencies=[Depends(RateLimiting(calls=5, period=300))],
)
async def verify_code(
    payload: VerifyCodeRequest, request: Request
) -> Any:
    client_ip = request.client.host if request.client else "unknown"
    return APIResponse(
        data=await SessionService.verify_reset_code(payload.token, client_ip),
        message="Xác thực mã bảo mật hoàn tất",
        status=status.HTTP_200_OK,
    )

@router.post("/dang-xuat", response_model=APIResponse[Any])
async def logout(response: Response, current_user: CurrentUser = Depends(get_current_user)):
    response.delete_cookie("doclib_refresh_token", path="/")
    return APIResponse(
        data=await SessionService.revoke_session(current_user),
        message="Đăng xuất hoàn tất",
    )

@router.post("/dang-xuat-tat-ca", response_model=APIResponse[Any])
async def logout_all(response: Response, current_user: CurrentUser = Depends(get_current_user)):
    response.delete_cookie("doclib_refresh_token", path="/")
    return APIResponse(
        data=await SessionService.revoke_all_sessions(current_user),
        message="Đăng xuất khỏi tất cả thiết bị hoàn tất",
    )


@router.post(
    "/lam-moi-phien",
    response_model=APIResponse[Any],
    dependencies=[Depends(RateLimiting(calls=20, period=60))],
)
async def refresh_session(
    request: Request,
    response: Response,
    doclib_refresh_token: str | None = Cookie(default=None),
):
    if not doclib_refresh_token:
        raise HTTPException(status_code=401, detail="Không tìm thấy phiên làm mới")
    client_ip = request.client.host if request.client else "unknown"
    token_data = await SessionService.refresh_session(doclib_refresh_token, client_ip)
    return APIResponse(
        data=set_refresh_cookie(response, request, token_data),
        message="Làm mới phiên đăng nhập hoàn tất",
        status=status.HTTP_200_OK,
    )
