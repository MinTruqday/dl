import os
from datetime import timedelta
from typing import Optional

from pydantic import BaseModel


class Settings(BaseModel):
    PROJECT_NAME: str = os.environ["PROJECT_NAME"]
    VERSION: str = os.environ["VERSION"]
    SECRET_KEY: str = os.environ["SECRET_KEY"]
    CORS_ALLOWED_ORIGINS: str = os.environ["CORS_ALLOWED_ORIGINS"]
    INTERNAL_REQUEST_TIMEOUT_SECONDS: float = float(
        os.environ["INTERNAL_REQUEST_TIMEOUT_SECONDS"]
    )
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.environ["ACCESS_TOKEN_EXPIRE_MINUTES"])
    REFRESH_TOKEN_EXPIRE_DAYS: int = int(os.environ["REFRESH_TOKEN_EXPIRE_DAYS"])
    EMAIL_VERIFICATION_EXPIRE_MINUTES: int = int(
        os.environ["EMAIL_VERIFICATION_EXPIRE_MINUTES"]
    )
    PASSWORD_RESET_EXPIRE_MINUTES: int = int(
        os.environ["PASSWORD_RESET_EXPIRE_MINUTES"]
    )
    PASSWORD_RESET_CODE_DIGITS: int = int(os.environ["PASSWORD_RESET_CODE_DIGITS"])
    PASSKEY_CHALLENGE_EXPIRE_SECONDS: int = int(
        os.environ["PASSKEY_CHALLENGE_EXPIRE_SECONDS"]
    )
    ADMIN_OPERATION_EXPIRE_MINUTES: int = int(
        os.environ["ADMIN_OPERATION_EXPIRE_MINUTES"]
    )
    MONGODB_URI: str = os.environ["MONGODB_URI"]
    REDIS_URI: str = os.environ["REDIS_URI"]
    GOOGLE_CLIENT_ID: Optional[str] = os.environ["GOOGLE_CLIENT_ID"]
    GOOGLE_CLIENT_SECRET: Optional[str] = os.environ["GOOGLE_CLIENT_SECRET"]
    GOOGLE_REDIRECT_URI: Optional[str] = os.environ["GOOGLE_REDIRECT_URI"]
    GOOGLE_AUTH_URL: str = os.environ["GOOGLE_AUTH_URL"]
    GOOGLE_TOKEN_URL: str = os.environ["GOOGLE_TOKEN_URL"]
    GOOGLE_USERINFO_URL: str = os.environ["GOOGLE_USERINFO_URL"]
    GOOGLE_OAUTH_STATE_EXPIRE_SECONDS: int = int(
        os.environ["GOOGLE_OAUTH_STATE_EXPIRE_SECONDS"]
    )
    PASSKEY_RP_ID: str = os.environ["PASSKEY_RP_ID"]
    PASSKEY_RP_NAME: str = os.environ["PASSKEY_RP_NAME"]
    PASSKEY_ALLOWED_ORIGINS: str = os.environ["PASSKEY_ALLOWED_ORIGINS"]
    SMTP_HOST: str = os.environ["SMTP_HOST"]
    SMTP_PORT: int = int(os.environ["SMTP_PORT"])
    SMTP_TIMEOUT_SECONDS: float = float(os.environ["SMTP_TIMEOUT_SECONDS"])
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
    AI_PROVIDER: str = os.environ["AI_PROVIDER"]
    AI_PROVIDER_CONFIGURED: bool = os.environ["AI_PROVIDER_CONFIGURED"].lower() == "true"
    LLM_MODEL: str = os.environ["LLM_MODEL"]
    MODEL_TIMEOUT_SECONDS: int = int(os.environ["MODEL_TIMEOUT_SECONDS"])
    AGENT_DEFAULT_MAX_OUTPUT_TOKENS: int = int(
        os.environ["AGENT_DEFAULT_MAX_OUTPUT_TOKENS"]
    )
    DEFAULT_STORAGE_LIMIT_BYTES: int = int(os.environ["DEFAULT_STORAGE_LIMIT_BYTES"])
    MAX_STORAGE_LIMIT_BYTES: int = int(os.environ["MAX_STORAGE_LIMIT_BYTES"])
    EMBEDDING_MODEL: str = os.environ["EMBEDDING_MODEL"]
    RERANKER_MODEL: str = os.environ["RERANKER_MODEL"]

    @property
    def refresh_token_expire_seconds(self) -> int:
        return int(timedelta(days=self.REFRESH_TOKEN_EXPIRE_DAYS).total_seconds())


settings = Settings()
