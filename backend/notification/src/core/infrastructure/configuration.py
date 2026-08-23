import os
from pydantic import BaseModel


def get_service_url(service_name_underscore: str) -> str:
    override = os.getenv(f"{service_name_underscore.upper()}_URL")
    if override: return override
    return f"http://{service_name_underscore.lower()}:8000"

class Settings(BaseModel):
    PROJECT_NAME: str = os.environ["PROJECT_NAME"]
    VERSION: str = os.environ["VERSION"]
    SECRET_KEY: str = os.environ["SECRET_KEY"]
    CORS_ALLOWED_ORIGINS: str = os.environ["CORS_ALLOWED_ORIGINS"]
    MONGODB_URI: str = os.environ["MONGODB_URI"]
    REDIS_URI: str = os.environ["REDIS_URI"]
    PLATFORM_SYSTEM_ID: str = os.environ["PLATFORM_SYSTEM_ID"]
    NOTIFICATION_DB_NAME: str = os.environ["NOTIFICATION_DB_NAME"]
    AUTHENTICATION_URL: str = get_service_url("AUTHENTICATION")

settings = Settings()
