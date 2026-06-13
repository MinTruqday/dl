import os
import secrets
import uuid
from datetime import datetime, timedelta, timezone

from core.config import settings
from core.database import db_client
from core.schemas.user import RoleEnum, UserCreate, UserInDB
from core.security import create_access_token, get_password_hash, verify_password
from fastapi import HTTPException, status
from loguru import logger
from src.repositories.auth_repository import AuthRepository
from src.services.email_service import EmailService
from uuid6 import uuid7


class AuthService:

    @staticmethod
    async def get_google_auth_url(db=None):
        google_client_id = settings.GOOGLE_CLIENT_ID
        redirect_uri = settings.GOOGLE_REDIRECT_URI
        if not google_client_id or not redirect_uri:
            logger.error("Chưa thiết lập khóa ứng dụng Google hoặc đường dẫn phản hồi")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Dịch vụ đăng nhập Google chưa được thiết lập",
            )
        auth_url = f"{settings.GOOGLE_AUTH_URL}?response_type=code&client_id={settings.GOOGLE_CLIENT_ID}&redirect_uri={settings.GOOGLE_REDIRECT_URI}&scope=openid email profile"
        return auth_url

    @staticmethod
    async def register_user(user_in: UserCreate, client_ip: str, db=None):
        config = await AuthRepository.get_system_config(db=db)
        if config and (not config.get("registration_enabled", True)):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Cổng đăng ký đang tạm đóng",
            )
        import httpx

        try:
            async with httpx.AsyncClient() as client:
                resp = await client.post(
                    "{settings.PROVISION_URL}/user/create",
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
                        resp.json().get("detail") if resp.json() else "Lỗi hệ thống"
                    )
                    raise HTTPException(status_code=400, detail=detail)
                elif resp.status_code != 201:
                    raise HTTPException(status_code=500, detail="Lỗi hệ thống")
                user_id = resp.json().get("data", {}).get("user_id")
        except httpx.RequestError:
            raise HTTPException(
                status_code=500, detail="Lỗi kết nối dịch vụ quản lý người dùng"
            )

        auth_cred = {
            "_id": user_id,
            "email": user_in.email,
            "password_hash": get_password_hash(user_in.password),
            "passkeys": [],
        }
        await AuthRepository.create_auth_credential(auth_cred, db=db)

        await AuthRepository.insert_audit_log(
            {
                "action": "REGISTER_USER",
                "actor_email": user_in.email,
                "ip": client_ip,
                "timestamp": datetime.now(timezone.utc),
            },
            db=db,
        )
        logger.info(f"Người dùng {user_in.email} đăng ký từ {client_ip}")
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
                        f"{settings.PROVISION_URL}/user/email/{username}",
                        timeout=settings.DEFAULT_HTTP_TIMEOUT,
                    )
                else:
                    resp = await client.get(
                        f"{settings.PROVISION_URL}/user/slug/{username}",
                        timeout=settings.DEFAULT_HTTP_TIMEOUT,
                    )
                if resp.status_code == 200:
                    user_doc = resp.json().get("data")
        except Exception:
            pass

        if not user_doc:
            raise HTTPException(
                status_code=401, detail="Tài khoản hoặc email không tồn tại"
            )

        auth_cred = await AuthRepository.get_auth_credential_by_id(
            str(user_doc["_id"]), db=db
        )
        password_hash = auth_cred.get("password_hash") if auth_cred else "invalid"

        if not verify_password(password, password_hash):
            await AuthRepository.insert_audit_log(
                {
                    "action": "LOGIN_FAILED_WRONG_PASSWORD",
                    "actor_email": user_doc["email"],
                    "ip": client_ip,
                    "timestamp": datetime.now(timezone.utc),
                },
                db=db,
            )
            logger.warning(
                f"Tài khoản {username} đăng nhập sai mật khẩu từ {client_ip}"
            )
            raise HTTPException(status_code=401, detail="Mật khẩu không chính xác")
        if not user_doc.get("is_active", True):
            raise HTTPException(status_code=403, detail="Tài khoản đang bị khóa")
        session_id = str(uuid7())
        user_id_str = str(user_doc["_id"])
        await AuthRepository.register_session(user_id_str, session_id, client_ip)
        access_token = create_access_token(
            data={"sub": user_doc["email"], "sid": session_id}
        )
        logger.info(f"Tài khoản {username} đăng nhập từ {client_ip}")
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
        await AuthRepository.revoke_all_sessions(user_id_str)
        logger.info(f"Vô hiệu hóa toàn bộ phiên đăng nhập của {user_id_str}")
        return {"message": "Đăng xuất khỏi tất cả thiết bị thành công"}

    @staticmethod
    async def forgot_password(email: str, client_ip: str, db=None):
        import httpx

        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(
                    f"{settings.PROVISION_URL}/user/email/{email}",
                    timeout=settings.DEFAULT_HTTP_TIMEOUT,
                )
                user = resp.json().get("data") if resp.status_code == 200 else None
        except Exception:
            user = None
        if user:
            otp_code = "".join([str(secrets.randbelow(10)) for _ in range(6)])
            await AuthRepository.create_password_reset_token(
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
            await AuthRepository.insert_audit_log(
                {
                    "action": "FORGOT_PASSWORD_REQUEST",
                    "actor_email": email,
                    "ip": client_ip,
                    "timestamp": datetime.now(timezone.utc),
                },
                db=db,
            )
            try:
                await EmailService.send_reset_password_email(email, otp_code)
            except Exception as e:
                logger.error("Lỗi gửi thư khôi phục mật khẩu")
        return {"status": "ok", "message": "Yêu cầu khôi phục mật khẩu đang được xử lý"}

    @staticmethod
    async def reset_password(token: str, new_password: str, client_ip: str, db=None):
        token_doc = await AuthRepository.get_valid_password_reset_token(token, db=db)
        if not token_doc or token_doc.get("expires_at") < datetime.now(timezone.utc):
            raise HTTPException(
                status_code=400, detail="Mã xác thực không hợp lệ hoặc đã hết hạn"
            )
        auth_cred = await AuthRepository.get_auth_credential_by_email(
            token_doc["email"], db=db
        )
        if auth_cred:
            await AuthRepository.update_password_hash(
                token_doc["email"], get_password_hash(new_password), db=db
            )
        await AuthRepository.mark_password_reset_token_used(token_doc["_id"], db=db)
        await AuthRepository.insert_audit_log(
            {
                "action": "RESET_PASSWORD_SUCCESS",
                "actor_email": token_doc["email"],
                "ip": client_ip,
                "timestamp": datetime.now(timezone.utc),
            },
            db=db,
        )
        logger.info(f"Tài khoản {token_doc['email']} đổi mật khẩu từ {client_ip}")
        return {"status": "ok", "message": "Thay đổi mật khẩu thành công"}

    @staticmethod
    async def verify_reset_code(token: str, client_ip: str, db=None):
        token_doc = await AuthRepository.get_valid_password_reset_token(token, db=db)
        if not token_doc or token_doc.get("expires_at") < datetime.now(timezone.utc):
            raise HTTPException(
                status_code=400, detail="Mã xác thực không hợp lệ hoặc đã hết hạn"
            )
        return {"status": "ok", "message": "Mã xác thực hợp lệ"}

    @staticmethod
    async def issue_token_for_user(user_doc: dict, client_ip: str, db=None):
        if not user_doc.get("is_active", True):
            raise HTTPException(status_code=403, detail="Tài khoản đang bị khóa")
        session_id = str(uuid7())
        user_id_str = str(user_doc["_id"])
        await AuthRepository.register_session(user_id_str, session_id, client_ip)
        access_token = create_access_token(
            data={"sub": user_doc["email"], "sid": session_id}
        )
        auth_cred = await AuthRepository.get_auth_credential_by_id(
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
                logger.error("Lỗi xác thực Google")
                raise HTTPException(status_code=400, detail="Xác thực Google thất bại")
            user_resp = await client.get(
                settings.GOOGLE_USERINFO_URL,
                headers={"Authorization": f"Bearer {token_data['access_token']}"},
            )
            google_user = user_resp.json()
        email = google_user.get("email")
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(
                    f"{settings.PROVISION_URL}/user/email/{email}",
                    timeout=settings.DEFAULT_HTTP_TIMEOUT,
                )
                user_doc = resp.json().get("data") if resp.status_code == 200 else None
        except Exception:
            user_doc = None
        if not user_doc:
            config = await AuthRepository.get_system_config(db=db)
            if config and (not config.get("registration_enabled", True)):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Cổng đăng ký đang tạm đóng",
                )
            import httpx

            try:
                async with httpx.AsyncClient() as client:
                    resp = await client.post(
                        "{settings.PROVISION_URL}/user/create",
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
                    if resp.status_code != 201:
                        raise HTTPException(
                            status_code=500, detail="Lỗi hệ thống khi tạo tài khoản"
                        )
                    user_id = resp.json().get("data", {}).get("user_id")

                    auth_cred = {
                        "_id": user_id,
                        "email": email,
                        "password_hash": "google_oauth_no_password",
                        "passkeys": [],
                    }
                    await AuthRepository.create_auth_credential(auth_cred, db=db)
                    user_doc = {"_id": user_id, "email": email, "is_active": True}
            except httpx.RequestError:
                raise HTTPException(
                    status_code=500, detail="Lỗi kết nối dịch vụ quản lý người dùng"
                )
            logger.info(f"Tạo tài khoản Google cho {email}")
        return await AuthService.issue_token_for_user(user_doc, client_ip)
