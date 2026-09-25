import os

from pydantic import BaseModel


class Settings(BaseModel):
    PROJECT_NAME: str = os.environ["PROJECT_NAME"]
    VERSION: str = os.environ["VERSION"]
    SECRET_KEY: str = os.environ["SECRET_KEY"]
    CORS_ALLOWED_ORIGINS: str = os.environ["CORS_ALLOWED_ORIGINS"]
    INTERNAL_REQUEST_TIMEOUT_SECONDS: float = float(
        os.environ["INTERNAL_REQUEST_TIMEOUT_SECONDS"]
    )
    MONGODB_URI: str = os.environ["MONGODB_URI"]
    REDIS_URI: str = os.environ["REDIS_URI"]
    PLATFORM_SYSTEM_ID: str = os.environ["PLATFORM_SYSTEM_ID"]
    NOTIFICATION_DB_NAME: str = os.environ["NOTIFICATION_DB_NAME"]
    AUTHENTICATION_URL: str = os.environ["AUTHENTICATION_URL"]


settings = Settings()
