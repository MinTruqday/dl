import secrets
import uuid
from datetime import datetime, timezone
from urllib.parse import urlencode

import httpx
from fastapi import HTTPException, status
from loguru import logger

from src.core.infrastructure.configuration import settings
from src.core.infrastructure.redis import redis
from src.repositories.identity import IdentityRepository


class GoogleService:
    @staticmethod
    async def get_google_auth_url():
        if not settings.GOOGLE_CLIENT_ID or not settings.GOOGLE_REDIRECT_URI:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Hệ thống chưa được cấu hình dịch vụ xác thực liên kết",
            )
        state = secrets.token_urlsafe(32)
        await redis.setex(f"google_oauth_state:{state}", 600, "valid")
        query = urlencode(
            {
                "response_type": "code",
                "client_id": settings.GOOGLE_CLIENT_ID,
                "redirect_uri": settings.GOOGLE_REDIRECT_URI,
                "scope": "openid email profile",
                "state": state,
                "prompt": "select_account",
            }
        )
        return f"{settings.GOOGLE_AUTH_URL}?{query}"

    @staticmethod
    async def handle_google_callback(code: str, state: str, client_ip: str):
        from src.services.session import SessionService

        if not code or not state:
            raise HTTPException(status_code=400, detail="Yêu cầu xác thực liên kết không hợp lệ")
        state_key = f"google_oauth_state:{state}"
        stored_state = await redis.get_client().getdel(state_key)
        if not stored_state:
            raise HTTPException(
                status_code=400, detail="Phiên xác thực liên kết không hợp lệ hoặc đã hết hạn"
            )
        if not all(
            [settings.GOOGLE_CLIENT_ID, settings.GOOGLE_CLIENT_SECRET, settings.GOOGLE_REDIRECT_URI]
        ):
            raise HTTPException(
                status_code=503, detail="Dịch vụ xác thực liên kết chưa được cấu hình"
            )

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
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
                token_resp.raise_for_status()
                access_token = token_resp.json().get("access_token")
                if not access_token:
                    raise HTTPException(
                        status_code=400, detail="Nhà cung cấp đã từ chối yêu cầu xác thực"
                    )
                user_resp = await client.get(
                    settings.GOOGLE_USERINFO_URL,
                    headers={"Authorization": f"Bearer {access_token}"},
                )
                user_resp.raise_for_status()
                google_user = user_resp.json()
        except HTTPException:
            raise
        except httpx.HTTPError:
            logger.exception("Federated identity provider request failed")
            raise HTTPException(
                status_code=502, detail="Không thể xác minh tài khoản với nhà cung cấp"
            )

        email = str(google_user.get("email", "")).strip().lower()
        if not email or google_user.get("email_verified") is not True:
            raise HTTPException(
                status_code=400, detail="Địa chỉ thư điện tử liên kết chưa được xác minh"
            )

        user_doc = await IdentityRepository.get_auth_credential_by_email(email)
        if not user_doc:
            config = await IdentityRepository.get_system_config()
            if config and not config.get("registration_enabled", True):
                raise HTTPException(
                    status_code=403,
                    detail="Tính năng đăng ký tài khoản mới tạm thời bị vô hiệu hóa",
                )
            slug = f"{email.split('@')[0]}_{secrets.token_hex(4)}"
            created_at = datetime.now(timezone.utc)
            user_id = str(uuid.uuid4())
            user_doc = {
                "_id": user_id,
                "email": email,
                "full_name": google_user.get("name") or email.split("@")[0],
                "slug": slug,
                "role": "reader",
                "system_role": "USER",
                "permissions": [],
                "is_active": True,
                "password_hash": None,
                "passkeys": [],
                "provider": "google",
                "created_at": created_at,
                "updated_at": created_at,
            }
            try:
                await IdentityRepository.create_auth_credential(user_doc)
            except HTTPException:
                raise
            except Exception:
                logger.exception("Federated user provisioning failed")
                raise HTTPException(
                    status_code=503, detail="Không thể thiết lập tài khoản liên kết"
                )

        return await SessionService.issue_token_for_user(user_doc, client_ip)
