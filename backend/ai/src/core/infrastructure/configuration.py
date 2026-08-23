import os
import tempfile
from typing import Optional

from pydantic import BaseModel


def get_service_url(service_name_underscore: str) -> str:
    override = os.getenv(f"{service_name_underscore.upper()}_URL")
    if override:
        return override
    return f"http://{service_name_underscore.lower()}:8000"


def get_runtime_path(*parts: str) -> str:
    return os.path.join(tempfile.gettempdir(), *parts)


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
    DOCKER_HOST: str = os.environ["DOCKER_HOST"]
    MINIO_ENDPOINT: str = os.environ["MINIO_ENDPOINT"]
    MINIO_ACCESS_KEY: str = os.environ["MINIO_ACCESS_KEY"]
    MINIO_SECRET_KEY: str = os.environ["MINIO_SECRET_KEY"]
    MINIO_PRIVATE_BUCKET: str = os.environ["MINIO_PRIVATE_BUCKET"]
    MINIO_PUBLIC_BUCKET: str = os.environ["MINIO_PUBLIC_BUCKET"]
    MINIO_REGION: str = os.environ["MINIO_REGION"]
    MINIO_PUBLIC_URL: Optional[str] = os.environ["MINIO_PUBLIC_URL"]
    MIN_FILE_SIZE_BYTES: int = int(os.environ["MIN_FILE_SIZE_BYTES"])
    TAVILY_API_KEY: Optional[str] = os.environ["TAVILY_API_KEY"]
    HF_TOKEN: str = os.environ["HF_TOKEN"]
    PRIMARY_MODEL_STYLE: str = os.environ["PRIMARY_MODEL_STYLE"]
    PRIMARY_MODEL_URL: str = os.environ["PRIMARY_MODEL_URL"]
    PRIMARY_MODEL_HEALTH_URL: str = os.environ["PRIMARY_MODEL_HEALTH_URL"]
    PRIMARY_MODEL_API_TOKEN: str = os.environ["PRIMARY_MODEL_API_TOKEN"]
    LLM_MODEL: str = os.environ["LLM_MODEL"]
    MODEL_TIMEOUT_SECONDS: float = float(os.environ["MODEL_TIMEOUT_SECONDS"])
    MODEL_KEEP_ALIVE: str = os.environ["MODEL_KEEP_ALIVE"]
    RERANKER_MODEL: str = os.environ["RERANKER_MODEL"]
    NLI_MODEL_NAME: str = os.environ["NLI_MODEL_NAME"]
    PLATFORM_SYSTEM_ID: str = os.environ["PLATFORM_SYSTEM_ID"]
    RAG_URL: str = get_service_url("RAG")
    ASSESSMENT_URL: str = get_service_url("ASSESSMENT")
    AI_DB_NAME: str = os.environ["AI_DB_NAME"]
    CONTENT_URL: str = get_service_url("CONTENT")
    AGENT_SLOW_DURATION_MS_THRESHOLD: int = int(os.environ["AGENT_SLOW_DURATION_MS_THRESHOLD"])
    AGENT_ROUTE_CONFIDENCE_THRESHOLD: float = float(os.environ["AGENT_ROUTE_CONFIDENCE_THRESHOLD"])
    AGENT_EXECUTION_TIMEOUT_SECONDS: int = int(os.environ["AGENT_EXECUTION_TIMEOUT_SECONDS"])
    AGENT_RECURSION_LIMIT: int = int(os.environ["AGENT_RECURSION_LIMIT"])
    AGENT_MAX_CONTEXT_TOKENS: int = int(os.environ["AGENT_MAX_CONTEXT_TOKENS"])
    AGENT_HISTORY_MAX_TURNS: int = int(os.environ["AGENT_HISTORY_MAX_TURNS"])
    AGENT_DEFAULT_MAX_OUTPUT_TOKENS: int = int(os.environ["AGENT_DEFAULT_MAX_OUTPUT_TOKENS"])
    AGENT_FILE_ROOT: str = os.environ["AGENT_FILE_ROOT"]
    AGENT_ARCHIVE_MAX_FILES: int = int(os.environ["AGENT_ARCHIVE_MAX_FILES"])
    AGENT_ARCHIVE_MAX_UNCOMPRESSED_BYTES: int = int(
        os.environ["AGENT_ARCHIVE_MAX_UNCOMPRESSED_BYTES"]
    )
    AGENT_ARCHIVE_MAX_COMPRESSION_RATIO: float = float(
        os.environ["AGENT_ARCHIVE_MAX_COMPRESSION_RATIO"]
    )


settings = Settings()
