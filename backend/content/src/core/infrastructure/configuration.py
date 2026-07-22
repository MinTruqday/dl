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
    RABBITMQ_URI: str = os.getenv("RABBITMQ_URI", "amqp://guest:guest@rabbitmq:5672/")
    PAYOS_API_URL: str = os.getenv("PAYOS_API_URL", "")
    PLATFORM_SYSTEM_ID: str = os.getenv("PLATFORM_SYSTEM_ID", "")
    HUMANITY_URL: str = get_service_url("HUMANITY")
    AGENTIC_AI_URL: str = get_service_url("AGENTIC_AI")
    NOTIFICATION_URL: str = get_service_url("NOTIFICATION")
    MANAGEMENT_URL: str = get_service_url("MANAGEMENT")
    USAGE_URL: str = get_service_url("USAGE")
    CONTENT_DB_NAME: str = os.getenv("CONTENT_DB_NAME", "doclib_content")
    HUMANITY_DB_NAME: str = os.getenv("HUMANITY_DB_NAME", "doclib_humanity")
    FINANCE_DB_NAME: str = os.getenv("FINANCE_DB_NAME", "doclib_finance")
    DRM_DB_NAME: str = os.getenv("DRM_DB_NAME", "doclib_drm")
    MINIO_ENDPOINT: str = os.getenv("MINIO_ENDPOINT", "http://minio:9000")
    MINIO_PUBLIC_URL: str = os.getenv("MINIO_PUBLIC_URL", "")

settings = Settings()
