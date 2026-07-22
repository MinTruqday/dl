import os
from typing import Optional

from pydantic import BaseModel

def get_service_url(service_name_underscore: str) -> str:
    override = os.getenv(f"{service_name_underscore.upper()}_URL")
    if override: return override
    k8s_host = os.getenv(f"{service_name_underscore.upper()}_SERVICE_HOST")
    if k8s_host: return f"http://{k8s_host}:8000"
    return f"http://{service_name_underscore.lower()}:8000"

class Settings(BaseModel):
    PROJECT_NAME: str = os.getenv("PROJECT_NAME", "DocLib")
    VERSION: str = os.getenv("VERSION", "1.0.0")
    SECRET_KEY: str = os.getenv("SECRET_KEY", "")
    CORS_ALLOWED_ORIGINS: str = os.getenv("CORS_ALLOWED_ORIGINS", "")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
    REFRESH_TOKEN_EXPIRE_DAYS: int = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "7"))
    MONGODB_URI: str = os.getenv("MONGODB_URI", "mongodb://mongodb:27017/doclib")
    REDIS_URI: str = os.getenv("REDIS_URI", "redis://redis:6379/0")
    GOOGLE_CLIENT_ID: Optional[str] = os.getenv("GOOGLE_CLIENT_ID")
    GOOGLE_CLIENT_SECRET: Optional[str] = os.getenv("GOOGLE_CLIENT_SECRET")
    GOOGLE_REDIRECT_URI: Optional[str] = os.getenv("GOOGLE_REDIRECT_URI")
    GOOGLE_AUTH_URL: str = os.getenv("GOOGLE_AUTH_URL", "https://accounts.google.com/o/oauth2/v2/auth")
    GOOGLE_TOKEN_URL: str = os.getenv("GOOGLE_TOKEN_URL", "https://oauth2.googleapis.com/token")
    GOOGLE_USERINFO_URL: str = os.getenv("GOOGLE_USERINFO_URL", "https://openidconnect.googleapis.com/v1/userinfo")
    PASSKEY_RP_ID: str = os.getenv("PASSKEY_RP_ID", "localhost")
    PASSKEY_RP_NAME: str = os.getenv("PASSKEY_RP_NAME", "DocLib")
    PASSKEY_ALLOWED_ORIGINS: str = os.getenv("PASSKEY_ALLOWED_ORIGINS", "http://localhost:3000")
    SMTP_HOST: str = os.getenv("SMTP_HOST", "localhost")
    SMTP_PORT: int = int(os.getenv("SMTP_PORT", "587"))
    SMTP_USER: Optional[str] = os.getenv("SMTP_USER")
    SMTP_PASS: Optional[str] = os.getenv("SMTP_PASS")
    SENDER_EMAIL: Optional[str] = os.getenv("SENDER_EMAIL")
    SENDER_NAME: Optional[str] = os.getenv("SENDER_NAME")
    PLATFORM_SYSTEM_ID: str = os.getenv("PLATFORM_SYSTEM_ID", "")
    HUMANITY_URL: str = get_service_url("HUMANITY")
    USAGE_URL: str = get_service_url("USAGE")
    AUTHENTICATION_DB_NAME: str = os.getenv("AUTHENTICATION_DB_NAME", "doclib_authentication")

settings = Settings()
