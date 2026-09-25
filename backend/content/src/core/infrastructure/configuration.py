import os

from pydantic import BaseModel


class Settings(BaseModel):
    PROJECT_NAME: str = os.environ["PROJECT_NAME"]
    VERSION: str = os.environ["VERSION"]
    INTERNAL_API_URL: str = os.environ["INTERNAL_API_URL"]
    SECRET_KEY: str = os.environ["SECRET_KEY"]
    CORS_ALLOWED_ORIGINS: str = os.environ["CORS_ALLOWED_ORIGINS"]
    INTERNAL_REQUEST_TIMEOUT_SECONDS: float = float(
        os.environ["INTERNAL_REQUEST_TIMEOUT_SECONDS"]
    )
    MONGODB_URI: str = os.environ["MONGODB_URI"]
    REDIS_URI: str = os.environ["REDIS_URI"]
    RABBITMQ_URI: str = os.environ["RABBITMQ_URI"]
    PLATFORM_SYSTEM_ID: str = os.environ["PLATFORM_SYSTEM_ID"]
    AUTHENTICATION_URL: str = os.environ["AUTHENTICATION_URL"]
    AI_URL: str = os.environ["AI_URL"]
    NOTIFICATION_URL: str = os.environ["NOTIFICATION_URL"]
    DOCUMENT_PASSWORD_MAX_ATTEMPTS: int = int(os.environ["DOCUMENT_PASSWORD_MAX_ATTEMPTS"])
    DOCUMENT_PASSWORD_RATE_LIMIT_SECONDS: int = int(
        os.environ["DOCUMENT_PASSWORD_RATE_LIMIT_SECONDS"]
    )
    DOCUMENT_PREVIEW_DEFAULT_PAGES: int = int(os.environ["DOCUMENT_PREVIEW_DEFAULT_PAGES"])
    DOCUMENT_PREVIEW_CHARACTERS_PER_PAGE: int = int(
        os.environ["DOCUMENT_PREVIEW_CHARACTERS_PER_PAGE"]
    )
    DOCUMENT_PREVIEW_BLOCKS_PER_PAGE: int = int(
        os.environ["DOCUMENT_PREVIEW_BLOCKS_PER_PAGE"]
    )
    CONTENT_DB_NAME: str = os.environ["CONTENT_DB_NAME"]
    OBJECT_STORAGE_ENDPOINT: str = os.environ["OBJECT_STORAGE_ENDPOINT"]
    OBJECT_STORAGE_PUBLIC_URL: str = os.environ["OBJECT_STORAGE_PUBLIC_URL"]


settings = Settings()
