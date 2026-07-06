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
    RABBITMQ_URI: str = os.getenv("RABBITMQ_URI")
    PAYOS_API_URL: str = os.getenv("PAYOS_API_URL")
    MINIO_ENDPOINT: str = os.getenv("MINIO_ENDPOINT")
    MINIO_ACCESS_KEY: str = os.getenv("MINIO_ACCESS_KEY")
    MINIO_SECRET_KEY: str = os.getenv("MINIO_SECRET_KEY")
    MINIO_PRIVATE_BUCKET: str = os.getenv("MINIO_PRIVATE_BUCKET", "doclib-private")
    MINIO_PUBLIC_BUCKET: str = os.getenv("MINIO_PUBLIC_BUCKET", "doclib-public")
    MINIO_REGION: str = os.getenv("MINIO_REGION")
    MINIO_PUBLIC_URL: Optional[str] = os.getenv("MINIO_PUBLIC_URL")
    MIN_FILE_SIZE_BYTES: int = int(os.getenv("MIN_FILE_SIZE_BYTES"))
    INTERNAL_API_URL: str = os.getenv("INTERNAL_API_URL")
    SERVICE_DB_NAME: str = os.getenv("SERVICE_DB_NAME")

settings = Settings()
