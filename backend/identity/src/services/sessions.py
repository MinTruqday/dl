import os
import secrets
import uuid
from datetime import datetime, timedelta, timezone

from fastapi import HTTPException, status
from loguru import logger
from src.repositories.auth_data import AuthenticationData
from src.services.email_dispatch import EmailDelivery
from uuid6 import uuid7

from shared.infrastructure.config import settings
from shared.infrastructure.database import db_client
from src.schemas.identity import RoleEnum, UserCreate, UserInDB
from shared.security.access_control import create_access_token, get_password_hash, verify_password


class AuthenticationFlow:

    @staticmethod
    async def get_google_auth_url(db=None):
        google_client_id = settings.GOOGLE_CLIENT_ID
        redirect_uri = settings.GOOGLE_REDIRECT_URI
        if not google_client_id or not redirect_uri:
            logger.error("Lỗi cấu hình nhà cung cấp xác thực")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Chưa cấu hình xác thực bên ngoài",
            )
        auth_url = f"{settings.GOOGLE_AUTH_URL}?response_type=code&client_id={settings.GOOGLE_CLIENT_ID}&redirect_uri={settings.GOOGLE_REDIRECT_URI}&scope=openid email profile"
        return auth_url

    @staticmethod
    async def register_user(user_in: UserCreate, client_ip: str, db=None):
        config = await AuthenticationData.get_system_config(db=db)
        if config and (not config.get("registration_enabled", True)):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Tạo tài khoản tạm thời bị vô hiệu hóa",
            )
        import httpx

        try:
            async with httpx.AsyncClient() as client:
                resp = await client.post(
                    f"{settings.ADMINISTRATION_URL}/nguoi-dung/",
                    json={
                        "email": user_in.email,
                        "full_name": user_in.full_name,
                        "slug": user_in.slug,
                        "role": "READER",
                    },
                    timeout=settings.DEFAULT_HTTP_TIMEOUT,
                )
                if resp.status_code == 400:

                    detail = (
                        resp.json().get("detail").replace(".", "")
                        if resp.json()
                        else "An unexpected system error occurred while attempting to process the registration request"
                    )
                    raise HTTPException(status_code=400, detail=detail)
                elif resp.status_code not in (200, 201):
                    raise HTTPException(status_code=500, detail="Lỗi kết nối tài khoản")
                user_id = resp.json().get("data", {}).get("user_id")
        except httpx.RequestError:
            raise HTTPException(
                status_code=500, detail="Lỗi kết nối quản lý người dùng"
            )

        auth_cred = {
            "_id": user_id,
            "email": user_in.email,
            "password_hash": get_password_hash(user_in.password),
            "passkeys": [],
        }
        await AuthenticationData.create_auth_credential(auth_cred, db=db)

        await AuthenticationData.insert_audit_log(
            {
                "action": "REGISTER_USER",
                "actor_email": user_in.email,
                "ip": client_ip,
                "timestamp": datetime.now(timezone.utc),
            },
            db=db,
        )
        logger.info("Đăng ký tài khoản mới thành công")
        return {
            "email": user_in.email,
            "full_name": user_in.full_name,
            "slug": user_in.slug,
            "role": "READER",
            "id": user_id,
        }

    @staticmethod
    async def login_user(username: str, password: str, client_ip: str, db=None):
        is_email = "@" in username
        import httpx

        user_doc = None
        try:
            async with httpx.AsyncClient() as client:
                if is_email:
                    resp = await client.get(
                        f"{settings.ADMINISTRATION_URL}/nguoi-dung/email/{username}",
                        timeout=settings.DEFAULT_HTTP_TIMEOUT,
                    )
                else:
                    resp = await client.get(
                        f"{settings.ADMINISTRATION_URL}/nguoi-dung/ten-mien/{username}",
                        timeout=settings.DEFAULT_HTTP_TIMEOUT,
                    )
                if resp.status_code == 200:
                    user_doc = resp.json().get("data")
        except Exception:
            pass

        if not user_doc:
            raise HTTPException(status_code=401, detail="Không tìm thấy tài khoản")

        auth_cred = await AuthenticationData.get_auth_credential_by_id(
            str(user_doc["_id"]), db=db
        )
        password_hash = auth_cred.get("password_hash") if auth_cred else "invalid"

        if not verify_password(password, password_hash):
            await AuthenticationData.insert_audit_log(
                {
                    "action": "LOGIN_FAILED_WRONG_PASSWORD",
                    "actor_email": user_doc["email"],
                    "ip": client_ip,
                    "timestamp": datetime.now(timezone.utc),
                },
                db=db,
            )
            logger.warning("Đăng nhập thất bại do sai thông tin xác thực")
            raise HTTPException(
                status_code=401, detail="Thông tin đăng nhập không chính xác"
            )
        if not user_doc.get("is_active", True):
            raise HTTPException(
                status_code=403, detail="Tài khoản đang bị khóa hoặc không hoạt động"
            )
        session_id = str(uuid7())
        user_id_str = str(user_doc["_id"])
        await AuthenticationData.register_session(user_id_str, session_id, client_ip)
        access_token = create_access_token(
            data={
                "sub": user_doc["email"],
                "sid": session_id,
                "role": user_doc.get("role", "reader"),
                "uid": str(user_doc.get("_id", "")),
                "permissions": user_doc.get("permissions", []),
                "is_premium": user_doc.get("is_premium", False),
                "full_name": user_doc.get("full_name", ""),
                "slug": user_doc.get("slug", ""),
            }
        )
        logger.info("Đăng nhập thành công")
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user": {
                "email": user_doc["email"],
                "has_passkey": len(auth_cred.get("passkeys", [])) > 0,
            },
        }

    @staticmethod
    async def revoke_all_sessions(current_user: UserInDB, db=None):
        user_id_str = str(current_user.id)
        await AuthenticationData.revoke_all_sessions(user_id_str)
        logger.info("Đã thu hồi tất cả phiên đăng nhập của tài khoản")
        return {"message": "Đã đăng xuất khỏi tất cả thiết bị"}

    @staticmethod
    async def forgot_password(email: str, client_ip: str, db=None):
        import httpx

        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(
                    f"{settings.ADMINISTRATION_URL}/nguoi-dung/email/{email}",
                    timeout=settings.DEFAULT_HTTP_TIMEOUT,
                )
                user = resp.json().get("data") if resp.status_code == 200 else None
        except Exception:
            user = None
        if user:
            otp_code = "".join([str(secrets.randbelow(10)) for _ in range(6)])
            await AuthenticationData.create_password_reset_token(
                {
                    "_id": secrets.token_hex(8),
                    "email": email,
                    "token": otp_code,
                    "expires_at": datetime.now(timezone.utc) + timedelta(minutes=1),
                    "used": False,
                    "created_at": datetime.now(timezone.utc),
                },
                db=db,
            )
            await AuthenticationData.insert_audit_log(
                {
                    "action": "FORGOT_PASSWORD_REQUEST",
                    "actor_email": email,
                    "ip": client_ip,
                    "timestamp": datetime.now(timezone.utc),
                },
                db=db,
            )
            try:
                await EmailDelivery.send_reset_password_email(email, otp_code)
            except Exception:
                logger.error("Lỗi gửi email khôi phục mật khẩu")
        return {"status": "ok", "message": "Đang xử lý yêu cầu khôi phục mật khẩu"}

    @staticmethod
    async def reset_password(token: str, new_password: str, client_ip: str, db=None):
        token_doc = await AuthenticationData.get_valid_password_reset_token(token, db=db)
        if not token_doc or token_doc.get("expires_at") < datetime.now(timezone.utc):
            raise HTTPException(
                status_code=400, detail="Mã xác minh không hợp lệ hoặc đã hết hạn"
            )
        auth_cred = await AuthenticationData.get_auth_credential_by_email(
            token_doc["email"], db=db
        )
        if auth_cred:
            await AuthenticationData.update_password_hash(
                token_doc["email"], get_password_hash(new_password), db=db
            )
        await AuthenticationData.mark_password_reset_token_used(token_doc["_id"], db=db)
        await AuthenticationData.insert_audit_log(
            {
                "action": "RESET_PASSWORD_SUCCESS",
                "actor_email": token_doc["email"],
                "ip": client_ip,
                "timestamp": datetime.now(timezone.utc),
            },
            db=db,
        )
        logger.info("Đổi mật khẩu thành công")
        return {"status": "ok", "message": "Cập nhật mật khẩu thành công"}

    @staticmethod
    async def verify_reset_code(token: str, client_ip: str, db=None):
        token_doc = await AuthenticationData.get_valid_password_reset_token(token, db=db)
        if not token_doc or token_doc.get("expires_at") < datetime.now(timezone.utc):
            raise HTTPException(
                status_code=400, detail="Mã xác minh không hợp lệ hoặc đã hết hạn"
            )
        return {"status": "ok", "message": "Mã xác minh hợp lệ"}

    @staticmethod
    async def issue_token_for_user(user_doc: dict, client_ip: str, db=None):
        if not user_doc.get("is_active", True):
            raise HTTPException(
                status_code=403, detail="Tài khoản đang bị khóa hoặc không hoạt động"
            )
        session_id = str(uuid7())
        user_id_str = str(user_doc["_id"])
        await AuthenticationData.register_session(user_id_str, session_id, client_ip)
        access_token = create_access_token(
            data={
                "sub": user_doc["email"],
                "sid": session_id,
                "role": user_doc.get("role", "reader"),
                "uid": str(user_doc.get("_id", "")),
                "permissions": user_doc.get("permissions", []),
                "is_premium": user_doc.get("is_premium", False),
                "full_name": user_doc.get("full_name", ""),
                "slug": user_doc.get("slug", ""),
            }
        )
        auth_cred = await AuthenticationData.get_auth_credential_by_id(
            str(user_doc["_id"]), db=db
        )
        has_passkey = len(auth_cred.get("passkeys", [])) > 0 if auth_cred else False
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user": {"email": user_doc["email"], "has_passkey": has_passkey},
        }

    @staticmethod
    async def handle_google_callback(code: str, client_ip: str, db=None):
        google_client_id = settings.GOOGLE_CLIENT_ID
        google_client_secret = settings.GOOGLE_CLIENT_SECRET
        redirect_uri = settings.GOOGLE_REDIRECT_URI
        import httpx

        async with httpx.AsyncClient() as client:
            token_resp = await client.post(
                settings.GOOGLE_TOKEN_URL,
                data={
                    "code": code,
                    "client_id": settings.GOOGLE_CLIENT_ID,
                    "client_secret": settings.GOOGLE_CLIENT_SECRET,
                    "redirect_uri": settings.GOOGLE_REDIRECT_URI,
                    "grant_type": "authorization_code",
                },
            )
            token_data = token_resp.json()
            if "access_token" not in token_data:
                logger.error("Từ chối yêu cầu xác thực")
                raise HTTPException(status_code=400, detail="Lỗi xác thực liên kết")
            user_resp = await client.get(
                settings.GOOGLE_USERINFO_URL,
                headers={"Authorization": f"Bearer {token_data['access_token']}"},
            )
            google_user = user_resp.json()
        email = google_user.get("email")
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(
                    f"{settings.ADMINISTRATION_URL}/nguoi-dung/email/{email}",
                    timeout=settings.DEFAULT_HTTP_TIMEOUT,
                )
                user_doc = resp.json().get("data") if resp.status_code == 200 else None
        except Exception:
            user_doc = None
        if not user_doc:
            config = await AuthenticationData.get_system_config(db=db)
            if config and (not config.get("registration_enabled", True)):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Tạo tài khoản tạm thời bị vô hiệu hóa",
                )
            import httpx

            try:
                async with httpx.AsyncClient() as client:
                    resp = await client.post(
                        f"{settings.ADMINISTRATION_URL}/nguoi-dung/",
                        json={
                            "email": email,
                            "full_name": google_user.get("name"),
                            "slug": google_user.get("email").split("@")[0]
                            + "_"
                            + secrets.token_hex(2),
                            "role": "READER",
                        },
                        timeout=settings.DEFAULT_HTTP_TIMEOUT,
                    )
                    if resp.status_code not in (200, 201):
                        raise HTTPException(
                            status_code=500, detail="Lỗi kết nối tài khoản"
                        )
                    user_id = resp.json().get("data", {}).get("user_id")

                    auth_cred = {
                        "_id": user_id,
                        "email": email,
                        "password_hash": "google_oauth_no_password",
                        "passkeys": [],
                    }
                    await AuthenticationData.create_auth_credential(auth_cred, db=db)
                    user_doc = {"_id": user_id, "email": email, "is_active": True}
            except httpx.RequestError:
                raise HTTPException(
                    status_code=500, detail="Lỗi kết nối quản lý người dùng"
                )
            logger.info("Tự động tạo tài khoản liên kết thành công")
        return await AuthenticationFlow.issue_token_for_user(user_doc, client_ip)
