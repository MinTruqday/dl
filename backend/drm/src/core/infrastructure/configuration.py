import os
from typing import Optional

from pydantic import BaseModel

class Settings(BaseModel):
    PROJECT_NAME: str = os.getenv("PROJECT_NAME")
    VERSION: str = os.getenv("VERSION")
    SECRET_KEY: str = os.getenv("SECRET_KEY")
    CORS_ALLOWED_ORIGINS: str = os.getenv("CORS_ALLOWED_ORIGINS")
    PLATFORM_SYSTEM_ID: str = os.getenv("PLATFORM_SYSTEM_ID")
    MONGODB_URI: str = os.getenv("MONGODB_URI")
    REDIS_URI: str = os.getenv("REDIS_URI")
    INTERNAL_API_URL: str = os.getenv("INTERNAL_API_URL")
    DEFAULT_PAGE_LIMIT: int = int(os.getenv("DEFAULT_PAGE_LIMIT"))
    MAX_PAGE_LIMIT: int = int(os.getenv("MAX_PAGE_LIMIT"))
    DEFAULT_HTTP_TIMEOUT: float = float(os.getenv("DEFAULT_HTTP_TIMEOUT"))
    LONG_PROCESS_TIMEOUT: float = float(os.getenv("LONG_PROCESS_TIMEOUT"))
    SERVICE_DB_NAME: str = os.getenv("SERVICE_DB_NAME")

settings = Settings()
