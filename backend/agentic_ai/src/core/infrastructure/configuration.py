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
    RABBITMQ_URI: str = os.getenv("RABBITMQ_URI")
    QDRANT_URL: str = os.getenv("QDRANT_URL")
    QDRANT_HOST: str = os.getenv("QDRANT_HOST")
    QDRANT_PORT: int = int(os.getenv("QDRANT_PORT"))
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
    HF_TOKEN: str = os.getenv("HF_TOKEN")
    LLM_MODEL: str = os.getenv("LLM_MODEL")
    QWEN_MODEL: str = os.getenv("QWEN_MODEL")
    EMBEDDING_MODEL: str = os.getenv("EMBEDDING_MODEL")
    RERANKER_MODEL: str = os.getenv("RERANKER_MODEL")
    NLLB_MODEL: str = os.getenv("NLLB_MODEL")
    NLI_MODEL_NAME: str = os.getenv("NLI_MODEL_NAME")
    CHANDRA_MODEL: str = os.getenv("CHANDRA_MODEL")
    PLATFORM_SYSTEM_ID: str = os.getenv("PLATFORM_SYSTEM_ID")
    MANAGEMENT_URL: str = get_service_url("MANAGEMENT")
    USAGE_URL: str = get_service_url("USAGE")
    DRM_URL: str = get_service_url("DRM")
    WEBSOCKET_URL: str = get_service_url("WEBSOCKET")
    AGENTIC_AI_DB_NAME: str = os.getenv("AGENTIC_AI_DB_NAME")
    FINETUNE_MODELS_DIR: str = os.getenv("FINETUNE_MODELS_DIR")
    FINETUNE_ADAPTERS_DIR: str = os.getenv("FINETUNE_ADAPTERS_DIR")
    FINETUNE_GGUF_DIR: str = os.getenv("FINETUNE_GGUF_DIR")

settings = Settings()
