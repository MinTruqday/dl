from core.config import settings
from datetime import datetime, timedelta
import secrets
import uuid
import os
from fastapi import HTTPException, status
from core.database import db_client
from core.security import get_password_hash, verify_password, create_access_token
from models.user import UserCreate, UserInDB
from services.email import EmailService
from loguru import logger

class AuthenticationService:
    @staticmethod
    async def get_google_auth_url():
        google_client_id = getattr(settings, "GOOGLE_CLIENT_ID", None)
        redirect_uri = getattr(settings, "GOOGLE_REDIRECT_URI", None)
        if not google_client_id or not redirect_uri:
            logger.error("GOOGLE_CLIENT_ID or GOOGLE_REDIRECT_URI is not set")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
                detail="Dịch vụ đăng nhập Google chưa được thiết lập. Vui lòng liên hệ quản trị viên."
            )
        
        auth_url = (
            f"https://accounts.google.com/o/oauth2/v2/auth?"
            f"response_type=code&client_id={google_client_id}&"
            f"redirect_uri={redirect_uri}&scope=openid email profile"
        )
        return auth_url

    @staticmethod
    async def register_user(user_in: UserCreate, client_ip: str):
        db = db_client.mongodb[settings.MONGODB_DB_NAME]
        
        config = await db["settings"].find_one({"_id": "system_config"})
        if config and not config.get("registration_enabled", True):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, 
                detail="Cổng đăng ký thành viên hiện đang tạm đóng theo yêu cầu của hệ thống. Vui lòng quay lại sau."
            )

        users_col = db["users"]
        if await users_col.find_one({"email": user_in.email}):
            raise HTTPException(status_code=400, detail="Địa chỉ Email này đã được sử dụng bởi một tài khoản khác.")
        if await users_col.find_one({"slug": user_in.slug}):
            raise HTTPException(status_code=400, detail="Đường dẫn hồ sơ (slug) này đã tồn tại trên hệ thống.")
        
        tos_accepted_at = datetime.utcnow() if user_in.agreed_to_terms else None
        user_doc = UserInDB(
            **user_in.model_dump(exclude={"password", "agreed_to_terms", "tos_accepted_at"}), 
            password_hash=get_password_hash(user_in.password),
            tos_accepted_at=tos_accepted_at
        )
        await users_col.insert_one(user_doc.model_dump(by_alias=True))
        await db["audit_logs"].insert_one({
            "action": "REGISTER_USER", 
            "actor_email": user_in.email, 
            "ip": client_ip, 
            "timestamp": datetime.utcnow()
        })
        logger.info(f"New user registered: {user_in.email} from {client_ip}")
        return user_doc

    @staticmethod
    async def login_user(username: str, password: str, client_ip: str):
        db = db_client.mongodb[settings.MONGODB_DB_NAME]
        
        is_email = "@" in username
        if is_email:
            user_doc = await db["users"].find_one({"email": username})
            if not user_doc:
                raise HTTPException(status_code=401, detail="Địa chỉ Email này không tồn tại trên hệ thống.")
        else:
            user_doc = await db["users"].find_one({"slug": username})
            if not user_doc:
                raise HTTPException(status_code=401, detail="Tên tài khoản này không tồn tại trên hệ thống.")

        if not verify_password(password, user_doc["password_hash"]):
            await db["audit_logs"].insert_one({
                "action": "LOGIN_FAILED_WRONG_PASSWORD", 
                "actor_email": user_doc["email"], 
                "ip": client_ip, 
                "timestamp": datetime.utcnow()
            })
            logger.warning(f"Login failed: Incorrect password for - {username} from {client_ip}")
            raise HTTPException(status_code=401, detail="Mật khẩu bạn nhập không chính xác.")
        
        if not user_doc.get("is_active", True):
            raise HTTPException(status_code=403, detail="Tài khoản của bạn hiện đang bị tạm khóa. Vui lòng liên hệ quản trị viên.")
            
        session_id = str(uuid.uuid4())
        user_id_str = str(user_doc["_id"])
        if db_client.redis:
            await db_client.redis.sadd(f"user_sessions:{user_id_str}", session_id)
            await db_client.redis.setex(f"session_meta:{session_id}", 604800, client_ip)
            
        access_token = create_access_token(data={"sub": user_doc["email"], "sid": session_id})
        logger.info(f"User logged in: {username} from {client_ip}")
        return {
            "access_token": access_token, 
            "token_type": "bearer",
            "user": {
                "email": user_doc["email"],
                "has_passkey": len(user_doc.get("passkeys", [])) > 0
            }
        }

    @staticmethod
    async def revoke_all_sessions(current_user: UserInDB):
        if not db_client.redis:
            return {"message": "Tính năng này hiện đang bảo trì và tạm thời không khả dụng."}
        
        user_id_str = str(current_user.id)
        sessions = await db_client.redis.smembers(f"user_sessions:{user_id_str}")
        for sid in sessions:
            await db_client.redis.delete(f"session_meta:{sid}")
        await db_client.redis.delete(f"user_sessions:{user_id_str}")
        
        logger.info(f"All sessions revoked for user {user_id_str}")
        return {"message": "Bạn đã đăng xuất khỏi tất cả các thiết bị thành công."}

    @staticmethod
    async def forgot_password(email: str, client_ip: str):
        db = db_client.mongodb[settings.MONGODB_DB_NAME]
        user = await db["users"].find_one({"email": email})
        if user:
            otp_code = "".join([str(secrets.randbelow(10)) for _ in range(6)])
            await db["password_reset_tokens"].insert_one({
                "_id": secrets.token_hex(8),
                "email": email,
                "token": otp_code,
                "expires_at": datetime.utcnow() + timedelta(minutes=10),
                "used": False,
                "created_at": datetime.utcnow(),
            })
            await db["audit_logs"].insert_one({
                "action": "FORGOT_PASSWORD_REQUEST", 
                "actor_email": email, 
                "ip": client_ip, 
                "timestamp": datetime.utcnow()
            })
            try:
                await EmailService.send_reset_password_email(email, otp_code)
            except Exception as e:
                logger.error(f"Failed to send reset email to {email}: {e}")
        return {"status": "ok", "message": "Yêu cầu đã được ghi nhận. Nếu Email tồn tại trên hệ thống, mã xác thực sẽ được gửi tới bạn trong giây lát."}

    @staticmethod
    async def reset_password(token: str, new_password: str, client_ip: str):
        db = db_client.mongodb[settings.MONGODB_DB_NAME]
        token_doc = await db["password_reset_tokens"].find_one({"token": token, "used": False})
        if not token_doc or token_doc.get("expires_at") < datetime.utcnow():
            raise HTTPException(status_code=400, detail="Mã xác thực không hợp lệ hoặc đã hết hạn. Vui lòng yêu cầu mã mới.")
            
        await db["users"].update_one(
            {"email": token_doc["email"]}, 
            {"$set": {"password_hash": get_password_hash(new_password), "updated_at": datetime.utcnow()}}
        )
        await db["password_reset_tokens"].update_one({"_id": token_doc["_id"]}, {"$set": {"used": True}})
        await db["audit_logs"].insert_one({
            "action": "RESET_PASSWORD_SUCCESS", 
            "actor_email": token_doc["email"], 
            "ip": client_ip, 
            "timestamp": datetime.utcnow()
        })
        logger.info(f"Password reset success for: {token_doc['email']} from {client_ip}")
        return {"status": "ok", "message": "Mật khẩu của bạn đã được thay đổi thành công."}

    @staticmethod
    async def verify_reset_code(token: str, client_ip: str):
        db = db_client.mongodb[settings.MONGODB_DB_NAME]
        token_doc = await db["password_reset_tokens"].find_one({"token": token, "used": False})
        if not token_doc or token_doc.get("expires_at") < datetime.utcnow():
            raise HTTPException(status_code=400, detail="Mã xác thực không hợp lệ hoặc đã hết hạn.")
        
        return {"status": "ok", "message": "Mã xác thực hợp lệ."}

    @staticmethod
    async def get_featured_authors(limit: int = 5):
        db = db_client.mongodb[settings.MONGODB_DB_NAME]
        cursor = db["users"].find({"role": RoleEnum.AUTHOR, "is_active": True}).limit(limit)
        authors = await cursor.to_list(length=limit)
        return [{
            "id": str(a["_id"]),
            "full_name": a.get("full_name"),
            "slug": a.get("slug"),
            "avatar_url": a.get("avatar_url"),
            "bio": a.get("bio", "Chưa có thông tin giới thiệu.")
        } for a in authors]

    @staticmethod
    async def issue_token_for_user(user_doc: dict, client_ip: str):
        if not user_doc.get("is_active", True):
            raise HTTPException(status_code=403, detail="Tài khoản của bạn hiện đang bị tạm khóa.")
            
        session_id = str(uuid.uuid4())
        user_id_str = str(user_doc["_id"])
        if db_client.redis:
            await db_client.redis.sadd(f"user_sessions:{user_id_str}", session_id)
            await db_client.redis.setex(f"session_meta:{session_id}", 604800, client_ip)
            
        access_token = create_access_token(data={"sub": user_doc["email"], "sid": session_id})
        return {
            "access_token": access_token, 
            "token_type": "bearer",
            "user": {
                "email": user_doc["email"],
                "has_passkey": len(user_doc.get("passkeys", [])) > 0
            }
        }

    @staticmethod
    async def handle_google_callback(code: str, client_ip: str):
        google_client_id = getattr(settings, "GOOGLE_CLIENT_ID", None)
        google_client_secret = getattr(settings, "GOOGLE_CLIENT_SECRET", None)
        redirect_uri = getattr(settings, "GOOGLE_REDIRECT_URI", None)
        import httpx
        async with httpx.AsyncClient() as client:
            token_resp = await client.post("https://oauth2.googleapis.com/token", data={"code": code, "client_id": google_client_id, "client_secret": google_client_secret, "redirect_uri": redirect_uri, "grant_type": "authorization_code"})
            token_data = token_resp.json()
            if "access_token" not in token_data:
                logger.error(f"Google OAuth failed: {token_data}")
                raise HTTPException(status_code=400, detail="Quá trình xác thực với Google thất bại. Vui lòng thử lại.")
            user_resp = await client.get("https://www.googleapis.com/oauth2/v3/userinfo", headers={"Authorization": f"Bearer {token_data['access_token']}"})
            google_user = user_resp.json()
        db = db_client.mongodb[settings.MONGODB_DB_NAME]
        users_col = db["users"]
        email = google_user.get("email")
        user_doc = await users_col.find_one({"email": email})
        if not user_doc:
            config = await db["settings"].find_one({"_id": "system_config"})
            if config and not config.get("registration_enabled", True):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN, 
                    detail="Hệ thống hiện đang tạm đóng cổng đăng ký mới (bao gồm cả Google). Vui lòng quay lại sau."
                )

            user_id = str(uuid.uuid4())
            user_doc = {"_id": user_id, "email": email, "full_name": google_user.get("name"), "avatar_url": google_user.get("picture"), "slug": google_user.get("email").split("@")[0] + "_" + secrets.token_hex(2), "password_hash": "google_oauth_no_password", "role": RoleEnum.READER, "is_active": True, "created_at": datetime.utcnow(), "updated_at": datetime.utcnow()}
            await users_col.insert_one(user_doc)
            logger.info(f"New user created via Google login: {email}")
        
        return await AuthenticationService.issue_token_for_user(user_doc, client_ip)