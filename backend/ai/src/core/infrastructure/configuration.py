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
    NEO4J_URI: str = os.getenv("NEO4J_URI", "bolt://neo4j:7687")
    NEO4J_USER: str = os.getenv("NEO4J_USER", "neo4j")
    NEO4J_PASSWORD: str = os.getenv("NEO4J_PASSWORD", "")
    EMBEDDING_MODEL: str = os.environ["EMBEDDING_MODEL"]
    DOCKER_HOST: str = os.environ["DOCKER_HOST"]
    OBJECT_STORAGE_ENDPOINT: str = os.environ["OBJECT_STORAGE_ENDPOINT"]
    OBJECT_STORAGE_ACCESS_KEY: str = os.environ["OBJECT_STORAGE_ACCESS_KEY"]
    OBJECT_STORAGE_SECRET_KEY: str = os.environ["OBJECT_STORAGE_SECRET_KEY"]
    OBJECT_STORAGE_PRIVATE_BUCKET: str = os.environ["OBJECT_STORAGE_PRIVATE_BUCKET"]
    OBJECT_STORAGE_PUBLIC_BUCKET: str = os.environ["OBJECT_STORAGE_PUBLIC_BUCKET"]
    OBJECT_STORAGE_REGION: str = os.environ["OBJECT_STORAGE_REGION"]
    OBJECT_STORAGE_PUBLIC_URL: Optional[str] = os.environ["OBJECT_STORAGE_PUBLIC_URL"]
    MIN_FILE_SIZE_BYTES: int = int(os.environ["MIN_FILE_SIZE_BYTES"])
    TAVILY_API_KEY: Optional[str] = os.environ["TAVILY_API_KEY"]
    HF_TOKEN: str = os.environ["HF_TOKEN"]
    HF_INFERENCE_URL: str = os.environ["HF_INFERENCE_URL"]
    PRIMARY_MODEL_URL: str = os.environ["PRIMARY_MODEL_URL"]
    PRIMARY_MODEL_HEALTH_URL: str = os.environ["PRIMARY_MODEL_HEALTH_URL"]
    LLM_MODEL: str = os.environ["LLM_MODEL"]
    MODEL_TIMEOUT_SECONDS: float = float(os.environ["MODEL_TIMEOUT_SECONDS"])
    RERANKER_MODEL: str = os.environ["RERANKER_MODEL"]
    NLI_MODEL_NAME: str = os.environ["NLI_MODEL_NAME"]
    PLATFORM_SYSTEM_ID: str = os.environ["PLATFORM_SYSTEM_ID"]
    AI_DB_NAME: str = os.environ["AI_DB_NAME"]
    CONTENT_URL: str = get_service_url("CONTENT")
    AI_REQUEST_TIMEOUT_SECONDS: float = float(os.getenv("AI_REQUEST_TIMEOUT_SECONDS", "900"))
    AGENT_SLOW_DURATION_MS_THRESHOLD: int = int(os.environ["AGENT_SLOW_DURATION_MS_THRESHOLD"])
    AGENT_ROUTE_CONFIDENCE_THRESHOLD: float = float(os.environ["AGENT_ROUTE_CONFIDENCE_THRESHOLD"])
    AGENT_EXECUTION_TIMEOUT_SECONDS: int = int(os.environ["AGENT_EXECUTION_TIMEOUT_SECONDS"])
    AGENT_RECURSION_LIMIT: int = int(os.environ["AGENT_RECURSION_LIMIT"])
    AGENT_MAX_CONTEXT_TOKENS: int = int(os.environ["AGENT_MAX_CONTEXT_TOKENS"])
    AGENT_HISTORY_MAX_TURNS: int = int(os.environ["AGENT_HISTORY_MAX_TURNS"])
    AGENT_DEFAULT_MAX_OUTPUT_TOKENS: int = int(os.environ["AGENT_DEFAULT_MAX_OUTPUT_TOKENS"])
    AGENT_MAX_SUPERVISOR_STEPS: int = int(os.getenv("AGENT_MAX_SUPERVISOR_STEPS", "12"))
    AGENT_MAX_SPECIALIST_STEPS: int = int(os.getenv("AGENT_MAX_SPECIALIST_STEPS", "8"))
    AGENT_MAX_TOOL_CALLS_PER_TASK: int = int(os.getenv("AGENT_MAX_TOOL_CALLS_PER_TASK", "6"))
    AGENT_MAX_TOOL_ERRORS: int = int(os.getenv("AGENT_MAX_TOOL_ERRORS", "2"))
    AGENT_MAX_RETRIES: int = int(os.getenv("AGENT_MAX_RETRIES", "2"))
    AGENT_TASK_TIMEOUT_SECONDS: int = int(os.getenv("AGENT_TASK_TIMEOUT_SECONDS", "300"))
    AGENT_MAX_EVIDENCE_ITEMS: int = int(os.getenv("AGENT_MAX_EVIDENCE_ITEMS", "100"))
    AGENT_FILE_ROOT: str = os.environ["AGENT_FILE_ROOT"]
    AGENT_ARCHIVE_MAX_FILES: int = int(os.environ["AGENT_ARCHIVE_MAX_FILES"])
    AGENT_ARCHIVE_MAX_UNCOMPRESSED_BYTES: int = int(
        os.environ["AGENT_ARCHIVE_MAX_UNCOMPRESSED_BYTES"]
    )
    AGENT_ARCHIVE_MAX_COMPRESSION_RATIO: float = float(
        os.environ["AGENT_ARCHIVE_MAX_COMPRESSION_RATIO"]
    )


settings = Settings()
