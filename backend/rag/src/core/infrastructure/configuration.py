import os
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
    QDRANT_URL: str = os.environ["QDRANT_URL"]
    NEO4J_URI: str = os.environ["NEO4J_URI"]
    NEO4J_USER: str = os.environ["NEO4J_USER"]
    NEO4J_PASSWORD: str = os.environ["NEO4J_PASSWORD"]
    MINIO_ENDPOINT: str = os.environ["MINIO_ENDPOINT"]
    MINIO_ACCESS_KEY: str = os.environ["MINIO_ACCESS_KEY"]
    MINIO_SECRET_KEY: str = os.environ["MINIO_SECRET_KEY"]
    MINIO_PRIVATE_BUCKET: str = os.environ["MINIO_PRIVATE_BUCKET"]
    MINIO_PUBLIC_BUCKET: str = os.environ["MINIO_PUBLIC_BUCKET"]
    EMBEDDING_MODEL: str = os.environ["EMBEDDING_MODEL"]
    RERANKER_MODEL: str = os.environ["RERANKER_MODEL"]
    PLATFORM_SYSTEM_ID: str = os.environ["PLATFORM_SYSTEM_ID"]
    CONTENT_URL: str = get_service_url("CONTENT")
    DRM_URL: str = get_service_url("DRM")
    AGENTIC_AI_URL: str = get_service_url("AGENTIC_AI")
    RAG_DB_NAME: str = os.environ["RAG_DB_NAME"]

settings = Settings()
