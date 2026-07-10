import httpx
import secrets
from src.core.logic_logger import log_logic_execution
from fastapi import HTTPException, status
from loguru import logger
from src.core.infrastructure.configuration import settings
from src.repositories.identity import IdentityRepository as AuthenticationRepository

class GoogleService:
    @staticmethod
    @log_logic_execution
    async def get_google_auth_url():
        google_client_id = settings.GOOGLE_CLIENT_ID
        redirect_uri = settings.GOOGLE_REDIRECT_URI
        if not google_client_id or not redirect_uri:
            logger.error("External authentication provider is missing or invalid")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Hệ thống chưa được cấu hình các dịch vụ xác thực liên kết bên ngoài",
            )
        auth_url = f"{settings.GOOGLE_AUTH_URL}?response_type=code&client_id={settings.GOOGLE_CLIENT_ID}&redirect_uri={settings.GOOGLE_REDIRECT_URI}&scope=openid email profile"
        return auth_url

    @staticmethod
    @log_logic_execution
    async def handle_google_callback(code: str, client_ip: str):
        from src.services.session import SessionService
        google_client_id = settings.GOOGLE_CLIENT_ID
        google_client_secret = settings.GOOGLE_CLIENT_SECRET
        redirect_uri = settings.GOOGLE_REDIRECT_URI
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
            token_data = token_resp.json()
            if "access_token" not in token_data:
                logger.warning("External authentication request was rejected by the provider")
                raise HTTPException(status_code=400, detail="Quá trình xác thực liên kết gặp sự cố")
            user_resp = await client.get(
                settings.GOOGLE_USERINFO_URL,
                headers={"Authorization": f"Bearer {token_data['access_token']}"},
            )
            google_user = user_resp.json()
        email = google_user.get("email")
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.get(
                    f"{settings.MANAGEMENT_URL}/nguoi-dung/email/{email}",
                )
                user_doc = resp.json().get("data") if resp.status_code == 200 else None
        except Exception:
            user_doc = None
        if not user_doc:
            config = await AuthenticationRepository.get_system_config()
            if config and (not config.get("registration_enabled", True)):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Tính năng đăng ký tài khoản mới tạm thời bị vô hiệu hóa trên hệ thống",
                )
            try:
                async with httpx.AsyncClient(timeout=10.0) as client:
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
                        timeout=10.0,
                    )
                    if resp.status_code not in (200, 201):
                        raise HTTPException(
                            status_code=500, detail="Quá trình thiết lập kết nối liên kết tài khoản gặp sự cố"
                        )
                    user_id = resp.json().get("data", {}).get("user_id")

                    auth_cred = {
                        "_id": user_id,
                        "email": email,
                        "password_hash": "google_oauth_no_password",
                        "passkeys": [],
                    }
                    await AuthenticationRepository.create_auth_credential(auth_cred)
                    user_doc = {"_id": user_id, "email": email, "is_active": True}
            except httpx.RequestError as e:
                raise HTTPException(
                    status_code=500, detail="Quá trình kết nối đến dịch vụ quản lý thông tin người dùng gặp sự cố"
                )
            logger.info("Automatic creation of federated user account completed successfully")
        return await SessionService.issue_token_for_user(user_doc, client_ip)
