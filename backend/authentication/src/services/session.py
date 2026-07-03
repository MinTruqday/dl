import os
import secrets
import uuid
from src.core.logic_logger import log_logic_execution
from datetime import datetime, timedelta, timezone

import httpx

from fastapi import HTTPException, status
from loguru import logger
from src.repositories.identity import IdentityRepository as AuthenticationRepository
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
        config = await AuthenticationRepository.get_system_config()
        if config and (not config.get("registration_enabled", True)):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Tạo tài khoản tạm thời bị vô hiệu hóa",
            )
        try:
            if await AuthenticationRepository.get_user_by_email(user_in.email):
                raise HTTPException(
                    status_code=400, detail="Tài khoản với email này đã tồn tại"
                )
            if await AuthenticationRepository.get_user_by_slug(user_in.slug):
                raise HTTPException(
                    status_code=400, detail="Tên người dùng đã được sử dụng"
                )
                
            user_id = str(uuid7())
            new_user = {
                "_id": user_id,
                "email": user_in.email,
                "full_name": user_in.full_name,
                "slug": user_in.slug,
                "role": "READER",
                "created_at": datetime.now(timezone.utc),
                "updated_at": datetime.now(timezone.utc),
                "is_active": True,
                "is_verified": False,
                "wallet_balance": 0,
                "is_premium": False,
                "storage_limit": 10737418240,
                "settings": {
                    "mod_notifs": True,
                    "auto_refresh": False,
                    "auto_save": True,
                    "default_visibility": "public"
                }
            }
            await AuthenticationRepository.create_user(new_user)
            
        except HTTPException as he:
            raise he
        except Exception as e:
            logger.exception("Lỗi tạo người dùng")
            raise HTTPException(status_code=500, detail="Lỗi hệ thống khi tạo người dùng")

        auth_cred = {
            "_id": user_id,
            "email": user_in.email,
            "password_hash": get_password_hash(user_in.password),
            "passkeys": [],
        }
        await AuthenticationRepository.create_auth_credential(auth_cred)

        await AuthenticationRepository.insert_audit_log(
            {
                "action": "REGISTER_USER",
                "actor_email": user_in.email,
                "ip": client_ip,
                "timestamp": datetime.now(timezone.utc),
            },
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
    @log_logic_execution
    async def login_user(username: str, password: str, client_ip: str):
        is_email = "@" in username
        user_doc = None
        try:
            if is_email:
                user_doc = await AuthenticationRepository.get_user_by_email(username)
            else:
                user_doc = await AuthenticationRepository.get_user_by_slug(username)
        except Exception:
            pass

        if not user_doc:
            raise HTTPException(status_code=401, detail="Không tìm thấy tài khoản")

        auth_cred = await AuthenticationRepository.get_auth_credential_by_id(
            str(user_doc["_id"])
        )
        password_hash = auth_cred.get("password_hash") if auth_cred else "invalid"

        if not verify_password(password, password_hash):
            await AuthenticationRepository.insert_audit_log(
                {
                    "action": "LOGIN_FAILED_WRONG_PASSWORD",
                    "actor_email": user_doc["email"],
                    "ip": client_ip,
                    "timestamp": datetime.now(timezone.utc),
                },
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
        await AuthenticationRepository.register_session(user_id_str, session_id, client_ip)
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
    @log_logic_execution
    async def revoke_all_sessions(current_user: UserInDB):
        user_id_str = str(current_user.id)
        await AuthenticationRepository.revoke_all_sessions(user_id_str)
        logger.info("Đã thu hồi tất cả phiên đăng nhập của tài khoản")
        return {"message": "Đã đăng xuất khỏi tất cả thiết bị"}

    @staticmethod
    @log_logic_execution
    async def forgot_password(email: str, client_ip: str):
        try:
            user = await AuthenticationRepository.get_user_by_email(email)
        except Exception:
            user = None
        if user:
            otp_code = "".join([str(secrets.randbelow(10)) for _ in range(6)])
            await AuthenticationRepository.create_password_reset_token(
                {
                    "_id": secrets.token_hex(8),
                    "email": email,
                    "token": otp_code,
                    "expires_at": datetime.now(timezone.utc) + timedelta(minutes=1),
                    "used": False,
                    "created_at": datetime.now(timezone.utc),
                },
            )
            await AuthenticationRepository.insert_audit_log(
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
                logger.exception("Lỗi gửi thư điện tử khôi phục mật khẩu")
        return {"status": "ok", "message": "Đang xử lý yêu cầu khôi phục mật khẩu"}

    @staticmethod
    @log_logic_execution
    async def reset_password(token: str, new_password: str, client_ip: str):
        token_doc = await AuthenticationRepository.get_valid_password_reset_token(token)
        if not token_doc or token_doc.get("expires_at") < datetime.now(timezone.utc):
            raise HTTPException(
                status_code=400, detail="Mã xác minh không hợp lệ hoặc đã hết hạn"
            )
        auth_cred = await AuthenticationRepository.get_auth_credential_by_email(
            token_doc["email"]
        )
        if auth_cred:
            await AuthenticationRepository.update_password_hash(
                token_doc["email"], get_password_hash(new_password)
            )
        await AuthenticationRepository.mark_password_reset_token_used(token_doc["_id"])
        await AuthenticationRepository.insert_audit_log(
            {
                "action": "RESET_PASSWORD_SUCCESS",
                "actor_email": token_doc["email"],
                "ip": client_ip,
                "timestamp": datetime.now(timezone.utc),
            },
        )
        logger.info("Đổi mật khẩu thành công")
        return {"status": "ok", "message": "Cập nhật mật khẩu thành công"}

    @staticmethod
    @log_logic_execution
    async def verify_reset_code(token: str, client_ip: str):
        token_doc = await AuthenticationRepository.get_valid_password_reset_token(token)
        if not token_doc or token_doc.get("expires_at") < datetime.now(timezone.utc):
            raise HTTPException(
                status_code=400, detail="Mã xác minh không hợp lệ hoặc đã hết hạn"
            )
        return {"status": "ok", "message": "Mã xác minh hợp lệ"}

    @staticmethod
    @log_logic_execution
    async def issue_token_for_user(user_doc: dict, client_ip: str):
        if not user_doc.get("is_active", True):
            raise HTTPException(
                status_code=403, detail="Tài khoản đang bị khóa hoặc không hoạt động"
            )
        session_id = str(uuid7())
        user_id_str = str(user_doc["_id"])
        await AuthenticationRepository.register_session(user_id_str, session_id, client_ip)
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
        auth_cred = await AuthenticationRepository.get_auth_credential_by_id(
            str(user_doc["_id"])
        )
        has_passkey = len(auth_cred.get("passkeys", [])) > 0 if auth_cred else False
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user": {"email": user_doc["email"], "has_passkey": has_passkey},
        }

