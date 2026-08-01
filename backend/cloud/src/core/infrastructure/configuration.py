import os
from typing import Optional

from pydantic import BaseModel


def get_service_url(service_name_underscore: str) -> str:
    override = os.getenv(f"{service_name_underscore.upper()}_URL")
    if override:
        return override
    k8s_host = os.getenv(f"{service_name_underscore.upper()}_SERVICE_HOST")
    if k8s_host:
        return f"http://{k8s_host}:8000"
    return f"http://{service_name_underscore.lower()}:8000"

class Settings(BaseModel):
    PROJECT_NAME: str = os.getenv("PROJECT_NAME", "DocLib")
    VERSION: str = os.getenv("VERSION", "1.0.0")
    INTERNAL_API_URL: str = os.getenv("INTERNAL_API_URL", "http://traefik:8000")
    SECRET_KEY: str = os.getenv("SECRET_KEY", "")
    CORS_ALLOWED_ORIGINS: str = os.getenv("CORS_ALLOWED_ORIGINS", "")
    MONGODB_URI: str = os.getenv("MONGODB_URI", "mongodb://mongodb:27017/doclib")
    REDIS_URI: str = os.getenv("REDIS_URI", "redis://redis:6379/0")
    MINIO_ENDPOINT: str = os.getenv("MINIO_ENDPOINT", "http://minio:9000")
    MINIO_ACCESS_KEY: str = os.getenv("MINIO_ACCESS_KEY", "")
    MINIO_SECRET_KEY: str = os.getenv("MINIO_SECRET_KEY", "")
    MINIO_PRIVATE_BUCKET: str = os.getenv("MINIO_PRIVATE_BUCKET", "doclib-private")
    MINIO_PUBLIC_BUCKET: str = os.getenv("MINIO_PUBLIC_BUCKET", "doclib-public")
    MINIO_LEGACY_BUCKET: str = os.getenv("MINIO_LEGACY_BUCKET", "doclib-books")
    MINIO_REGION: str = os.getenv("MINIO_REGION", "us-east-1")
    MINIO_PUBLIC_URL: Optional[str] = os.getenv("MINIO_PUBLIC_URL")
    MIN_FILE_SIZE_BYTES: int = int(os.getenv("MIN_FILE_SIZE_BYTES", "1"))
    MAX_UPLOAD_SIZE_BYTES: int = int(os.getenv("MAX_UPLOAD_SIZE_BYTES", str(100 * 1024 * 1024)))
    PLATFORM_SYSTEM_ID: str = os.getenv("PLATFORM_SYSTEM_ID", "")
    MANAGEMENT_URL: str = get_service_url("MANAGEMENT")
    USAGE_URL: str = get_service_url("USAGE")
    CLOUD_DB_NAME: str = os.getenv("CLOUD_DB_NAME", "doclib_cloud")
    HUMANITY_DB_NAME: str = os.getenv("HUMANITY_DB_NAME", "doclib_humanity")
    USAGE_DB_NAME: str = os.getenv("USAGE_DB_NAME", "doclib_usage")
    MESSAGING_DB_NAME: str = os.getenv("MESSAGING_DB_NAME", "doclib_messaging")

settings = Settings()
