import os
from typing import Optional

from pydantic import BaseModel


def get_service_url(service_name_underscore: str) -> str:
    override = os.getenv(f"{service_name_underscore.upper()}_URL")
    if override:
        return override
    k8s_host = os.getenv(f"{service_name_underscore.upper()}_SERVICE_HOST")
    if k8s_host:
        k8s_port = os.getenv(f"{service_name_underscore.upper()}_SERVICE_PORT", "80")
        return f"http://{k8s_host}:{k8s_port}"
    return f"http://{service_name_underscore.lower()}:8000"

class Settings(BaseModel):
    PROJECT_NAME: str = os.environ["PROJECT_NAME"]
    VERSION: str = os.environ["VERSION"]
    INTERNAL_API_URL: str = os.environ["INTERNAL_API_URL"]
    SECRET_KEY: str = os.environ["SECRET_KEY"]
    CORS_ALLOWED_ORIGINS: str = os.environ["CORS_ALLOWED_ORIGINS"]
    MONGODB_URI: str = os.environ["MONGODB_URI"]
    REDIS_URI: str = os.environ["REDIS_URI"]
    RABBITMQ_URI: str = os.environ["RABBITMQ_URI"]
    PAYOS_API_URL: str = os.environ["PAYOS_API_URL"]
    PLATFORM_SYSTEM_ID: str = os.environ["PLATFORM_SYSTEM_ID"]
    HUMANITY_URL: str = get_service_url("HUMANITY")
    AGENTIC_AI_URL: str = get_service_url("AGENTIC_AI")
    NOTIFICATION_URL: str = get_service_url("NOTIFICATION")
    MANAGEMENT_URL: str = get_service_url("MANAGEMENT")
    USAGE_URL: str = get_service_url("USAGE")
    CONTENT_DB_NAME: str = os.environ["CONTENT_DB_NAME"]
    HUMANITY_DB_NAME: str = os.environ["HUMANITY_DB_NAME"]
    FINANCE_DB_NAME: str = os.environ["FINANCE_DB_NAME"]
    DRM_DB_NAME: str = os.environ["DRM_DB_NAME"]
    MINIO_ENDPOINT: str = os.environ["MINIO_ENDPOINT"]
    MINIO_PUBLIC_URL: str = os.environ["MINIO_PUBLIC_URL"]

settings = Settings()
