import os
from typing import Optional

from pydantic import BaseModel

def get_service_url(service_name_underscore: str) -> str:
    override = os.getenv(f"{service_name_underscore.upper()}_URL")
    if override: return override
    k8s_host = os.getenv(f"{service_name_underscore.upper()}_SERVICE_HOST")
    if k8s_host:
        k8s_port = os.getenv(f"{service_name_underscore.upper()}_SERVICE_PORT", "80")
        return f"http://{k8s_host}:{k8s_port}"
    return f"http://{service_name_underscore.lower()}:8000"

class Settings(BaseModel):
    PROJECT_NAME: str = os.environ["PROJECT_NAME"]
    VERSION: str = os.environ["VERSION"]
    SECRET_KEY: str = os.environ["SECRET_KEY"]
    CORS_ALLOWED_ORIGINS: str = os.environ["CORS_ALLOWED_ORIGINS"]
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.environ["ACCESS_TOKEN_EXPIRE_MINUTES"])
    REFRESH_TOKEN_EXPIRE_DAYS: int = int(os.environ["REFRESH_TOKEN_EXPIRE_DAYS"])
    MONGODB_URI: str = os.environ["MONGODB_URI"]
    REDIS_URI: str = os.environ["REDIS_URI"]
    GOOGLE_CLIENT_ID: Optional[str] = os.environ["GOOGLE_CLIENT_ID"]
    GOOGLE_CLIENT_SECRET: Optional[str] = os.environ["GOOGLE_CLIENT_SECRET"]
    GOOGLE_REDIRECT_URI: Optional[str] = os.environ["GOOGLE_REDIRECT_URI"]
    GOOGLE_AUTH_URL: str = os.environ["GOOGLE_AUTH_URL"]
    GOOGLE_TOKEN_URL: str = os.environ["GOOGLE_TOKEN_URL"]
    GOOGLE_USERINFO_URL: str = os.environ["GOOGLE_USERINFO_URL"]
    PASSKEY_RP_ID: str = os.environ["PASSKEY_RP_ID"]
    PASSKEY_RP_NAME: str = os.environ["PASSKEY_RP_NAME"]
    PASSKEY_ALLOWED_ORIGINS: str = os.environ["PASSKEY_ALLOWED_ORIGINS"]
    SMTP_HOST: str = os.environ["SMTP_HOST"]
    SMTP_PORT: int = int(os.environ["SMTP_PORT"])
    SMTP_USER: Optional[str] = os.environ["SMTP_USER"]
    SMTP_PASS: Optional[str] = os.environ["SMTP_PASS"]
    SENDER_EMAIL: Optional[str] = os.environ["SENDER_EMAIL"]
    SENDER_NAME: Optional[str] = os.environ["SENDER_NAME"]
    PLATFORM_SYSTEM_ID: str = os.environ["PLATFORM_SYSTEM_ID"]
    HUMANITY_URL: str = get_service_url("HUMANITY")
    USAGE_URL: str = get_service_url("USAGE")
    AUTHENTICATION_DB_NAME: str = os.environ["AUTHENTICATION_DB_NAME"]

settings = Settings()
