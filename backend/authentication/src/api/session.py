from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Cookie, Depends, HTTPException, Request, Response, status
from fastapi.security import OAuth2PasswordRequestForm
from pymongo import ReturnDocument
from src.api.cookies import set_refresh_cookie
from src.core.infrastructure.database import database
from src.core.infrastructure.configuration import settings
from src.core.infrastructure.redis import redis
from src.core.security.access import get_password_hash, verify_password
from src.repositories.identity import IdentityRepository
from src.services.session import SessionService

from src.core.dependency import CurrentUser, RateLimiting, get_current_user
from src.core.response import APIResponse
from src.schemas.identity import (
    ForgotPasswordRequest,
    AccountDeactivate,
    EmailChange,
    NotificationSettingsUpdate,
    PasswordChange,
    ProfileUpdate,
    SettingsUpdate,
    ResetPasswordRequest,
    UserCreate,
    UserResponse,
    VerifyCodeRequest,
)

router = APIRouter(prefix="/xac-thuc")


@router.get("/ca-nhan", response_model=APIResponse[UserResponse])
async def read_users_me(current_user: CurrentUser = Depends(get_current_user)):
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
            "full_name": user_doc.get("full_name") or current_user.full_name or "Người dùng Veriq",
            "slug": user_doc.get("slug")
            or str(user_doc.get("email", current_user.email)).split("@", 1)[0],
            "role": user_doc.get("role", "reader"),
            "system_role": user_doc.get(
                "system_role",
                "ADMIN" if user_doc.get("role") == "admin" else "USER",
            ),
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


@router.patch("/ca-nhan", response_model=APIResponse[Any])
async def update_users_me(
    payload: ProfileUpdate,
    current_user: CurrentUser = Depends(get_current_user),
):
    changes = {
        key: value
        for key, value in payload.model_dump().items()
        if value is not None
    }
    if not changes:
        raise HTTPException(status_code=422, detail="Không có dữ liệu cần cập nhật")
    changes["updated_at"] = datetime.now(timezone.utc)
    account = await database.mongodb[
        settings.AUTHENTICATION_DB_NAME
    ].auth_credentials.find_one_and_update(
        {"_id": current_user.id},
        {"$set": changes},
        return_document=ReturnDocument.AFTER,
    )
    if not account:
        raise HTTPException(status_code=404, detail="Không tìm thấy tài khoản")
    await IdentityRepository.insert_audit_log(
        {
            "action": "ACCOUNT_PROFILE_UPDATED",
            "actor_email": current_user.email,
            "target_user_id": current_user.id,
            "changes": sorted(changes),
            "timestamp": datetime.now(timezone.utc),
        }
    )
    account["_id"] = str(account["_id"])
    account.pop("password_hash", None)
    account.pop("passkeys", None)
    return APIResponse(data=account, message="Cập nhật hồ sơ cá nhân hoàn tất")


@router.post("/doi-email", response_model=APIResponse[Any])
async def change_email(payload: EmailChange, current_user: CurrentUser = Depends(get_current_user)):
    account = await IdentityRepository.get_auth_credential_by_id(current_user.id)
    if not account or not verify_password(payload.current_password, account.get("password_hash", "")):
        raise HTTPException(status_code=403, detail="Mật khẩu hiện tại không chính xác")
    new_email = str(payload.new_email).lower()
    if new_email == current_user.email.lower():
        raise HTTPException(status_code=422, detail="Email mới phải khác email hiện tại")
    duplicate = await database.mongodb[settings.AUTHENTICATION_DB_NAME].auth_credentials.find_one({"email": new_email})
    if duplicate:
        raise HTTPException(status_code=409, detail="Email mới đã được sử dụng")
    await database.mongodb[settings.AUTHENTICATION_DB_NAME].auth_credentials.update_one(
        {"_id": current_user.id}, {"$set": {"email": new_email, "email_verified": False, "updated_at": datetime.now(timezone.utc)}}
    )
    await IdentityRepository.revoke_all_sessions(current_user.id)
    await IdentityRepository.insert_audit_log({"action": "ACCOUNT_EMAIL_CHANGED", "actor_email": current_user.email, "target_user_id": current_user.id, "new_email": new_email, "timestamp": datetime.now(timezone.utc)})
    return APIResponse(data={"email": new_email, "reauth_required": True}, message="Đổi email hoàn tất, vui lòng đăng nhập lại")


@router.get("/cai-dat", response_model=APIResponse[Any])
async def read_settings(current_user: CurrentUser = Depends(get_current_user)):
    account = await IdentityRepository.get_auth_credential_by_id(current_user.id)
    return APIResponse(data=account.get("preferences", {}) if account else {}, message="Tải cài đặt cá nhân hoàn tất")


@router.patch("/cai-dat", response_model=APIResponse[Any])
async def update_settings(payload: SettingsUpdate, current_user: CurrentUser = Depends(get_current_user)):
    values = {key: value for key, value in payload.model_dump().items() if value is not None}
    await database.mongodb[settings.AUTHENTICATION_DB_NAME].auth_credentials.update_one({"_id": current_user.id}, {"$set": {f"preferences.{key}": value for key, value in values.items()}})
    await IdentityRepository.insert_audit_log({"action": "ACCOUNT_PREFERENCES_UPDATED", "actor_email": current_user.email, "target_user_id": current_user.id, "changes": sorted(values), "timestamp": datetime.now(timezone.utc)})
    return APIResponse(data=values, message="Cập nhật cài đặt cá nhân hoàn tất")


@router.patch("/thong-bao", response_model=APIResponse[Any])
async def update_notifications(payload: NotificationSettingsUpdate, current_user: CurrentUser = Depends(get_current_user)):
    values = payload.model_dump()
    await database.mongodb[settings.AUTHENTICATION_DB_NAME].auth_credentials.update_one({"_id": current_user.id}, {"$set": {f"notification_settings.{key}": value for key, value in values.items()}})
    await IdentityRepository.insert_audit_log({"action": "ACCOUNT_NOTIFICATIONS_UPDATED", "actor_email": current_user.email, "target_user_id": current_user.id, "changes": sorted(values), "timestamp": datetime.now(timezone.utc)})
    return APIResponse(data=values, message="Cập nhật thông báo cá nhân hoàn tất")


@router.post("/vo-hieu-hoa", response_model=APIResponse[Any])
async def deactivate_account(payload: AccountDeactivate, current_user: CurrentUser = Depends(get_current_user)):
    account = await IdentityRepository.get_auth_credential_by_id(current_user.id)
    if not account or not verify_password(payload.current_password, account.get("password_hash", "")):
        raise HTTPException(status_code=403, detail="Mật khẩu hiện tại không chính xác")
    await database.mongodb[settings.AUTHENTICATION_DB_NAME].auth_credentials.update_one({"_id": current_user.id}, {"$set": {"is_active": False, "account_status": "DISABLED", "updated_at": datetime.now(timezone.utc)}})
    await IdentityRepository.revoke_all_sessions(current_user.id)
    await IdentityRepository.insert_audit_log({"action": "ACCOUNT_DEACTIVATED", "actor_email": current_user.email, "target_user_id": current_user.id, "timestamp": datetime.now(timezone.utc)})
    return APIResponse(data={"deactivated": True}, message="Vô hiệu hóa tài khoản hoàn tất")


@router.post("/doi-mat-khau", response_model=APIResponse[Any])
async def change_password(
    payload: PasswordChange,
    current_user: CurrentUser = Depends(get_current_user),
):
    account = await IdentityRepository.get_auth_credential_by_id(current_user.id)
    if not account or not verify_password(payload.current_password, account.get("password_hash", "")):
        raise HTTPException(status_code=403, detail="Mật khẩu hiện tại không chính xác")
    if verify_password(payload.new_password, account.get("password_hash", "")):
        raise HTTPException(status_code=422, detail="Mật khẩu mới phải khác mật khẩu hiện tại")
    timestamp = datetime.now(timezone.utc)
    await database.mongodb[settings.AUTHENTICATION_DB_NAME].auth_credentials.update_one(
        {"_id": current_user.id},
        {
            "$set": {
                "password_hash": get_password_hash(payload.new_password),
                "last_password_change": timestamp,
                "updated_at": timestamp,
            }
        },
    )
    await database.mongodb[settings.AUTHENTICATION_DB_NAME].sessions.update_many(
        {
            "user_id": current_user.id,
            "_id": {"$ne": current_user.session_id},
            "revoked_at": None,
        },
        {"$set": {"revoked_at": timestamp}},
    )
    await redis.delete(f"user_sessions:{current_user.id}")
    await redis.sadd(f"user_sessions:{current_user.id}", current_user.session_id)
    await redis.get_client().expire(
        f"user_sessions:{current_user.id}",
        settings.REFRESH_TOKEN_EXPIRE_DAYS * 86400,
    )
    await IdentityRepository.insert_audit_log(
        {
            "action": "ACCOUNT_PASSWORD_CHANGED",
            "actor_email": current_user.email,
            "target_user_id": current_user.id,
            "timestamp": timestamp,
        }
    )
    return APIResponse(
        data={"other_sessions_revoked": True},
        message="Đổi mật khẩu và thu hồi các phiên khác hoàn tất",
    )


@router.get("/phien", response_model=APIResponse[Any])
async def list_my_sessions(current_user: CurrentUser = Depends(get_current_user)):
    sessions = (
        await database.mongodb[settings.AUTHENTICATION_DB_NAME]
        .sessions.find(
            {"user_id": current_user.id},
            {"refresh_token_hash": 0},
        )
        .sort("created_at", -1)
        .to_list(500)
    )
    for session in sessions:
        session["is_current"] = session.get("_id") == current_user.session_id
    return APIResponse(data=sessions, message="Tải danh sách phiên đăng nhập hoàn tất")


@router.delete("/phien/{session_id}", response_model=APIResponse[Any])
async def revoke_my_session(
    session_id: str,
    current_user: CurrentUser = Depends(get_current_user),
):
    session = await database.mongodb[settings.AUTHENTICATION_DB_NAME].sessions.find_one(
        {"_id": session_id, "user_id": current_user.id}
    )
    if not session:
        raise HTTPException(status_code=404, detail="Không tìm thấy phiên đăng nhập")
    await IdentityRepository.revoke_session(current_user.id, session_id)
    await IdentityRepository.insert_audit_log(
        {
            "action": "ACCOUNT_SESSION_REVOKED",
            "actor_email": current_user.email,
            "target_user_id": current_user.id,
            "session_id": session_id,
            "timestamp": datetime.now(timezone.utc),
        }
    )
    return APIResponse(
        data={"revoked": True, "session_id": session_id},
        message="Thu hồi phiên đăng nhập hoàn tất",
    )

@router.post(
    "/dang-ky",
    response_model=APIResponse[UserResponse],
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(RateLimiting(calls=3, period=60))],
)
async def register_user(user_in: UserCreate, request: Request) -> Any:
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
    request: Request, response: Response, form_data: OAuth2PasswordRequestForm = Depends()
) -> Any:
    client_ip = request.client.host if request.client else "unknown"
    token_data = await SessionService.login_user(form_data.username, form_data.password, client_ip)
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
async def forgot_password(payload: ForgotPasswordRequest, request: Request) -> Any:
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
async def reset_password(payload: ResetPasswordRequest, request: Request) -> Any:
    client_ip = request.client.host if request.client else "unknown"
    return APIResponse(
        data=await SessionService.reset_password(payload.token, payload.new_password, client_ip),
        message="Thực hiện thay đổi mật khẩu tài khoản hoàn tất",
        status=status.HTTP_200_OK,
    )


@router.post(
    "/xac-nhan-ma",
    response_model=APIResponse[Any],
    dependencies=[Depends(RateLimiting(calls=5, period=300))],
)
async def verify_code(payload: VerifyCodeRequest, request: Request) -> Any:
    client_ip = request.client.host if request.client else "unknown"
    return APIResponse(
        data=await SessionService.verify_reset_code(payload.token, client_ip),
        message="Xác thực mã bảo mật hoàn tất",
        status=status.HTTP_200_OK,
    )


@router.post("/dang-xuat", response_model=APIResponse[Any])
async def logout(response: Response, current_user: CurrentUser = Depends(get_current_user)):
    response.delete_cookie("veriq_refresh_token", path="/")
    return APIResponse(
        data=await SessionService.revoke_session(current_user), message="Đăng xuất hoàn tất"
    )


@router.post("/dang-xuat-tat-ca", response_model=APIResponse[Any])
async def logout_all(response: Response, current_user: CurrentUser = Depends(get_current_user)):
    response.delete_cookie("veriq_refresh_token", path="/")
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
    request: Request, response: Response, veriq_refresh_token: str | None = Cookie(default=None)
):
    if not veriq_refresh_token:
        raise HTTPException(status_code=401, detail="Không tìm thấy phiên làm mới")
    client_ip = request.client.host if request.client else "unknown"
    token_data = await SessionService.refresh_session(veriq_refresh_token, client_ip)
    return APIResponse(
        data=set_refresh_cookie(response, request, token_data),
        message="Làm mới phiên đăng nhập hoàn tất",
        status=status.HTTP_200_OK,
    )
