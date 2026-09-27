import os
from typing import Optional

from pydantic import BaseModel

class Settings(BaseModel):
    PROJECT_NAME: str = os.environ["PROJECT_NAME"]
    VERSION: str = os.environ["VERSION"]
    SECRET_KEY: str = os.environ["SECRET_KEY"]
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.environ["ACCESS_TOKEN_EXPIRE_MINUTES"])
    REFRESH_TOKEN_EXPIRE_DAYS: int = int(os.environ["REFRESH_TOKEN_EXPIRE_DAYS"])
    CORS_ALLOWED_ORIGINS: str = os.environ["CORS_ALLOWED_ORIGINS"]
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
    AUTHENTICATION_DB_NAME: str = os.environ["AUTHENTICATION_DB_NAME"]
    AI_INTERNAL_URL: str = os.environ["AI_INTERNAL_URL"]
    AUTHENTICATION_INTERNAL_URL: str = os.environ["AUTHENTICATION_INTERNAL_URL"]
    CLOUD_INTERNAL_URL: str = os.environ["CLOUD_INTERNAL_URL"]
    CONTENT_INTERNAL_URL: str = os.environ["CONTENT_INTERNAL_URL"]
    TESTING_INTERNAL_URL: str = os.environ["TESTING_INTERNAL_URL"]
    WORKER_INTERNAL_URL: str = os.environ["WORKER_INTERNAL_URL"]
    LLM_MODEL: str = os.environ["LLM_MODEL"]
    EMBEDDING_MODEL: str = os.environ["EMBEDDING_MODEL"]
    RERANKER_MODEL: str = os.environ["RERANKER_MODEL"]

settings = Settings()
