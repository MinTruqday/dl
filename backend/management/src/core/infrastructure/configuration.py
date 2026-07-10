import os
from typing import Optional

from pydantic import BaseModel


def get_service_url(service_name_underscore: str) -> str:
    override = os.getenv(f"{service_name_underscore.upper()}_URL")
    if override: return override
    k8s_host = os.getenv(f"{service_name_underscore.upper()}_SERVICE_HOST")
    if k8s_host: return f"http://{k8s_host}:8000"
    return f"http://{service_name_underscore.lower()}:8000"

class Settings(BaseModel):
    PROJECT_NAME: str = os.getenv("PROJECT_NAME")
    VERSION: str = os.getenv("VERSION")
    INTERNAL_API_URL: str = os.getenv("INTERNAL_API_URL")
    SECRET_KEY: str = os.getenv("SECRET_KEY")
    CORS_ALLOWED_ORIGINS: str = os.getenv("CORS_ALLOWED_ORIGINS")
    MONGODB_URI: str = os.getenv("MONGODB_URI")
    REDIS_URI: str = os.getenv("REDIS_URI")
    PAYOS_API_URL: str = os.getenv("PAYOS_API_URL")
    MINIO_ENDPOINT: str = os.getenv("MINIO_ENDPOINT")
    MINIO_ACCESS_KEY: str = os.getenv("MINIO_ACCESS_KEY")
    MINIO_SECRET_KEY: str = os.getenv("MINIO_SECRET_KEY")
    MINIO_PRIVATE_BUCKET: str = os.getenv("MINIO_PRIVATE_BUCKET")
    MINIO_PUBLIC_BUCKET: str = os.getenv("MINIO_PUBLIC_BUCKET")
    MINIO_REGION: str = os.getenv("MINIO_REGION")
    MINIO_PUBLIC_URL: Optional[str] = os.getenv("MINIO_PUBLIC_URL")
    MIN_FILE_SIZE_BYTES: int = int(os.getenv("MIN_FILE_SIZE_BYTES"))
    TAVILY_API_KEY: Optional[str] = os.getenv("TAVILY_API_KEY")
    LLAMA_MODEL: str = os.getenv("LLAMA_MODEL", "meta-llama/Llama-4-Maverick-17B-128E-Instruct-FP8")
    QWEN_MODEL: str = os.getenv("QWEN_MODEL", "Qwen/Qwen3.6-35B-A3B")
    EMBEDDING_MODEL: str = os.getenv("EMBEDDING_MODEL", "BAAI/bge-m3")
    RERANKER_MODEL: str = os.getenv("RERANKER_MODEL", "BAAI/bge-reranker-v2-m3")
    PLATFORM_SYSTEM_ID: str = os.getenv("PLATFORM_SYSTEM_ID")
    AGENTIC_AI_URL: str = get_service_url("AGENTIC_AI")
    MANAGEMENT_DB_NAME: str = os.getenv("MANAGEMENT_DB_NAME")

settings = Settings()
