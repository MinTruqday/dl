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
    PLATFORM_SYSTEM_ID: str = os.getenv("PLATFORM_SYSTEM_ID", "")
    COMPILATION_URL: str = get_service_url("COMPILATION")
    CONTENT_URL: str = get_service_url("CONTENT")
    COMPILATION_DB_NAME: str = os.getenv("COMPILATION_DB_NAME", "doclib_compilation")
    CONTENT_DB_NAME: str = os.getenv("CONTENT_DB_NAME", "doclib_content")
    MINIO_ENDPOINT: str = os.getenv("MINIO_ENDPOINT", "http://minio:9000")
    MINIO_PUBLIC_URL: Optional[str] = os.getenv("MINIO_PUBLIC_URL")
    MAX_COMPILE_INPUT_BYTES: int = int(os.getenv("MAX_COMPILE_INPUT_BYTES", str(2 * 1024 * 1024)))
    MAX_COMPILE_OUTPUT_BYTES: int = int(os.getenv("MAX_COMPILE_OUTPUT_BYTES", str(50 * 1024 * 1024)))
    MAX_CONCURRENT_COMPILATIONS: int = int(os.getenv("MAX_CONCURRENT_COMPILATIONS", "2"))

settings = Settings()
