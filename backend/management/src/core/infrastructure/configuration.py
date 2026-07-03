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
    PAYOS_API_URL: str = os.getenv("PAYOS_API_URL")
    TAVILY_API_KEY: Optional[str] = os.getenv("TAVILY_API_KEY")
    MINIO_ENDPOINT: str = os.getenv("MINIO_ENDPOINT")
    MINIO_ACCESS_KEY: str = os.getenv("MINIO_ACCESS_KEY")
    MINIO_SECRET_KEY: str = os.getenv("MINIO_SECRET_KEY")
    MINIO_BUCKET_NAME: str = os.getenv("MINIO_BUCKET_NAME")
    MINIO_REGION: str = os.getenv("MINIO_REGION")
    MINIO_PUBLIC_URL: Optional[str] = os.getenv("MINIO_PUBLIC_URL")
    MIN_FILE_SIZE_BYTES: int = int(os.getenv("MIN_FILE_SIZE_BYTES"))
    INTERNAL_API_URL: str = os.getenv("INTERNAL_API_URL")
    AGENTIC_AI_URL: str = os.getenv("AGENTIC_AI_URL")
    DEFAULT_PAGE_LIMIT: int = int(os.getenv("DEFAULT_PAGE_LIMIT"))
    MAX_PAGE_LIMIT: int = int(os.getenv("MAX_PAGE_LIMIT"))
    DEFAULT_HTTP_TIMEOUT: float = float(os.getenv("DEFAULT_HTTP_TIMEOUT"))
    LONG_PROCESS_TIMEOUT: float = float(os.getenv("LONG_PROCESS_TIMEOUT"))

    MONGO_URL: str = os.getenv("MONGO_URL", "http://doclib_database:8800/co-so-du-lieu")
    QUEUE_URL: str = os.getenv("QUEUE_URL", "http://doclib_queue:8802/hang-doi")
    CACHE_URL: str = os.getenv("CACHE_URL", "http://doclib_cache:8801")
    SERVICE_DB_NAME: str = os.getenv("SERVICE_DB_NAME")

settings = Settings()
