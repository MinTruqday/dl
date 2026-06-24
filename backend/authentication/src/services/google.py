import httpx
import secrets
from fastapi import HTTPException, status
from loguru import logger
from src.core.infrastructure.configuration import settings
from src.repositories.authentication import AuthenticationRepository

class GoogleService:
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
    async def handle_google_callback(code: str, client_ip: str, db=None):
        from src.services.session import SessionService
        google_client_id = settings.GOOGLE_CLIENT_ID
        google_client_secret = settings.GOOGLE_CLIENT_SECRET
        redirect_uri = settings.GOOGLE_REDIRECT_URI
        async with httpx.AsyncClient(timeout=settings.DEFAULT_HTTP_TIMEOUT) as client:
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
            async with httpx.AsyncClient(timeout=settings.DEFAULT_HTTP_TIMEOUT) as client:
                resp = await client.get(
                    f"{settings.MANAGEMENT_URL}/nguoi-dung/email/{email}",
                )
                user_doc = resp.json().get("data") if resp.status_code == 200 else None
        except Exception:
            user_doc = None
        if not user_doc:
            config = await AuthenticationRepository.get_system_config(db=db)
            if config and (not config.get("registration_enabled", True)):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Tạo tài khoản tạm thời bị vô hiệu hóa",
                )
            try:
                async with httpx.AsyncClient(timeout=settings.DEFAULT_HTTP_TIMEOUT) as client:
                    resp = await client.post(
                        f"{settings.MANAGEMENT_URL}/nguoi-dung/",
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
                    await AuthenticationRepository.create_auth_credential(auth_cred, db=db)
                    user_doc = {"_id": user_id, "email": email, "is_active": True}
            except httpx.RequestError as e:
                raise HTTPException(
                    status_code=500, detail=f"Lỗi kết nối quản lý người dùng: {e}"
                )
            logger.info("Tự động tạo tài khoản liên kết thành công")
        return await SessionService.issue_token_for_user(user_doc, client_ip)
