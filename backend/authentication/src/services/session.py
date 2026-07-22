import os
import secrets
import uuid
from src.core.logic_logger import log_logic_execution
from datetime import datetime, timedelta, timezone

import httpx

from fastapi import HTTPException, status
from loguru import logger
from src.repositories.identity import IdentityRepository as IdentityRepository
from src.services.email import EmailService
from uuid6 import uuid7

from src.core.infrastructure.configuration import settings
from src.core.infrastructure.database import database
from src.schemas.identity import Role, UserCreate, UserInDB
from src.core.security.access import create_access_token, get_password_hash, verify_password

class SessionService:

    @staticmethod
    @log_logic_execution
    async def register_user(user_in: UserCreate, client_ip: str):
        config = await IdentityRepository.get_system_config()
        if config and (not config.get("registration_enabled", True)):
            raise HTTPException(status_code=403, detail="Tính năng đăng ký tài khoản mới tạm thời bị vô hiệu hóa trên hệ thống")

        if await IdentityRepository.get_auth_credential_by_email(user_in.email):
            raise HTTPException(status_code=400, detail="Địa chỉ thư điện tử đã được sử dụng cho một tài khoản khác")
        if await IdentityRepository.get_auth_credential_by_slug(user_in.slug):
            raise HTTPException(status_code=400, detail="Tên đăng nhập đã tồn tại trên hệ thống")

        import httpx
        humanity_url = settings.HUMANITY_URL + "/nguoi-dung/"
        async with httpx.AsyncClient() as client:
            try:
                resp = await client.post(humanity_url, json={
                    "email": user_in.email,
                    "full_name": user_in.full_name,
                    "slug": user_in.slug,
                    "role": "reader"
                }, timeout=10.0)
                if resp.status_code != 201:
                    raise HTTPException(status_code=400, detail="Quá trình khởi tạo hồ sơ người dùng gặp sự cố")
                user_id = resp.json()["data"]["user_id"]
            except Exception as e:
                logger.exception("Failed to execute external HTTP request to Humanity service for user registration")
                raise HTTPException(status_code=500, detail="Quá trình kết nối đến dịch vụ quản lý thông tin người dùng gặp sự cố")

        auth_cred = {
            "_id": user_id,
            "email": user_in.email,
            "slug": user_in.slug,
            "password_hash": get_password_hash(user_in.password),
            "passkeys": [],
        }
        await IdentityRepository.create_auth_credential(auth_cred)
        await IdentityRepository.insert_audit_log({
            "action": "REGISTER_USER",
            "actor_email": user_in.email,
            "ip": client_ip,
            "timestamp": datetime.now(timezone.utc),
        })
        logger.info("User account registration process completed successfully")
        return {
            "email": user_in.email,
            "full_name": user_in.full_name,
            "slug": user_in.slug,
            "role": "READER",
            "id": user_id,
        }

    @staticmethod
    @log_logic_execution
    async def login_user(username: str, password: str, client_ip: str):
        is_email = "@" in username
        try:
            if is_email:
                auth_cred = await IdentityRepository.get_auth_credential_by_email(username)
            else:
                auth_cred = await IdentityRepository.get_auth_credential_by_slug(username)
        except Exception:
            auth_cred = None

        if not auth_cred:
            raise HTTPException(status_code=401, detail="Không tìm thấy thông tin tài khoản người dùng")

        password_hash = auth_cred.get("password_hash") if auth_cred else "invalid"

        if not verify_password(password, password_hash):
            await IdentityRepository.insert_audit_log({
                "action": "LOGIN_FAILED_WRONG_PASSWORD",
                "actor_email": auth_cred.get("email", ""),
                "ip": client_ip,
                "timestamp": datetime.now(timezone.utc),
            })
            logger.warning("User authentication failed due to invalid credentials provided")
            raise HTTPException(status_code=401, detail="Thông tin đăng nhập không chính xác")
            
        user_id_str = str(auth_cred["_id"])
        
        import httpx
        internal_url = f"{settings.HUMANITY_URL}/nguoi-dung/email/{auth_cred['email']}"
        role = "reader"
        is_active = True
        user_data = {}
        ai_tier = "BASIC"
        
        async with httpx.AsyncClient() as client:
            try:
                resp = await client.get(internal_url, timeout=5.0)
                if resp.status_code == 200:
                    user_data = resp.json()["data"]
                    role = user_data.get("role", "reader")
                    is_active = user_data.get("is_active", True)
            except Exception as e:
                logger.exception("Failed to fetch user profile details from Humanity service during login")
                pass
            try:
                usage_response = await client.get(
                    f"{settings.USAGE_URL}/goi-cuoc/{user_id_str}",
                    timeout=5.0,
                )
                if usage_response.status_code == 200:
                    ai_tier = usage_response.json().get("data", {}).get(
                        "ai_tier", "BASIC"
                    )
            except Exception:
                logger.exception("Failed to fetch AI tier during login")

        if not is_active:
            raise HTTPException(status_code=403, detail="Tài khoản hiện đang bị khóa hoặc ở trạng thái không hoạt động")

        session_id = str(uuid7())
        from src.core.infrastructure.redis import redis
        await redis.sadd(f"user_sessions:{user_id_str}", session_id)
        await IdentityRepository.register_session(user_id_str, session_id, client_ip)
        access_token = create_access_token(
            data={
                "sub": auth_cred["email"],
                "sid": session_id,
                "role": role,
                "uid": user_id_str,
                "permissions": user_data.get("permissions", []),
                "is_premium": user_data.get("is_premium", False),
                "ai_tier": ai_tier,
                "full_name": user_data.get("full_name", ""),
                "slug": user_data.get("slug", ""),
            }
        )
        refresh_token = create_access_token(
            data={"sub": auth_cred["email"], "sid": session_id, "type": "refresh"},
            expires_delta=timedelta(days=7),
        )
        await IdentityRepository.insert_audit_log({
            "action": "LOGIN_SUCCESS",
            "actor_email": auth_cred["email"],
            "ip": client_ip,
            "timestamp": datetime.now(timezone.utc),
        })
        logger.info("User authentication process completed successfully")
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user": {
                "email": auth_cred["email"],
                "has_passkey": len(auth_cred.get("passkeys", [])) > 0,
            },
        }

    @staticmethod
    @log_logic_execution
    async def revoke_all_sessions(current_user: UserInDB):
        user_id_str = str(current_user.id)
        await IdentityRepository.revoke_all_sessions(user_id_str)
        logger.info("Revocation of all active user sessions completed successfully")
        return {"message": "Thực hiện đăng xuất khỏi tất cả các thiết bị hoàn tất"}

    @staticmethod
    @log_logic_execution
    async def forgot_password(email: str, client_ip: str):
        try:
            user = await IdentityRepository.get_user_by_email(email)
        except Exception:
            user = None
        if user:
            otp_code = "".join([str(secrets.randbelow(10)) for _ in range(6)])
            await IdentityRepository.create_password_reset_token(
                {
                    "_id": secrets.token_hex(8),
                    "email": email,
                    "token": otp_code,
                    "expires_at": datetime.now(timezone.utc) + timedelta(minutes=1),
                    "used": False,
                    "created_at": datetime.now(timezone.utc),
                },
            )
            await IdentityRepository.insert_audit_log(
                {
                    "action": "FORGOT_PASSWORD_REQUEST",
                    "actor_email": email,
                    "ip": client_ip,
                    "timestamp": datetime.now(timezone.utc),
                },
            )
            try:
                await EmailService.send_reset_password_email(email, otp_code)
            except Exception as e:
                logger.exception("Failed to dispatch password recovery email notification")
        return {"status": "ok", "message": "Hệ thống đang tiến hành xử lý yêu cầu khôi phục mật khẩu"}

    @staticmethod
    @log_logic_execution
    async def reset_password(token: str, new_password: str, client_ip: str):
        token_doc = await IdentityRepository.get_valid_password_reset_token(token)
        if not token_doc or token_doc.get("expires_at") < datetime.now(timezone.utc):
            raise HTTPException(
                status_code=400, detail="Mã xác minh bảo mật không hợp lệ hoặc đã quá hạn sử dụng"
            )
        auth_cred = await IdentityRepository.get_auth_credential_by_email(
            token_doc["email"]
        )
        if auth_cred:
            await IdentityRepository.update_password_hash(
                token_doc["email"], get_password_hash(new_password)
            )
        await IdentityRepository.mark_password_reset_token_used(token_doc["_id"])
        await IdentityRepository.insert_audit_log(
            {
                "action": "RESET_PASSWORD_SUCCESS",
                "actor_email": token_doc["email"],
                "ip": client_ip,
                "timestamp": datetime.now(timezone.utc),
            },
        )
        logger.info("User account password modification completed successfully")
        return {"status": "ok", "message": "Thực hiện thay đổi mật khẩu tài khoản hoàn tất"}

    @staticmethod
    @log_logic_execution
    async def verify_reset_code(token: str, client_ip: str):
        token_doc = await IdentityRepository.get_valid_password_reset_token(token)
        if not token_doc or token_doc.get("expires_at") < datetime.now(timezone.utc):
            raise HTTPException(
                status_code=400, detail="Mã xác minh bảo mật không hợp lệ hoặc đã quá hạn sử dụng"
            )
        return {"status": "ok", "message": "Xác thực mã bảo mật hoàn tất"}

    @staticmethod
    @log_logic_execution
    async def issue_token_for_user(user_doc: dict, client_ip: str):
        if not user_doc.get("is_active", True):
            raise HTTPException(
                status_code=403, detail="Tài khoản hiện đang bị khóa hoặc ở trạng thái không hoạt động"
            )
        session_id = str(uuid7())
        user_id_str = str(user_doc["_id"])
        await IdentityRepository.register_session(user_id_str, session_id, client_ip)
        access_token = create_access_token(
            data={
                "sub": user_doc["email"],
                "sid": session_id,
                "role": user_doc.get("role", "reader"),
                "uid": str(user_doc.get("_id", "")),
                "permissions": user_doc.get("permissions", []),
                "is_premium": user_doc.get("is_premium", False),
                "ai_tier": user_doc.get("ai_tier", "BASIC"),
                "full_name": user_doc.get("full_name", ""),
                "slug": user_doc.get("slug", ""),
            }
        )
        auth_cred = await IdentityRepository.get_auth_credential_by_id(
            str(user_doc["_id"])
        )
        has_passkey = len(auth_cred.get("passkeys", [])) > 0 if auth_cred else False
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user": {"email": user_doc["email"], "has_passkey": has_passkey},
        }
