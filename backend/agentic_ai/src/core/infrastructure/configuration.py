import os
import tempfile
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
    QDRANT_HOST: str = os.environ["QDRANT_HOST"]
    QDRANT_PORT: int = int(os.environ["QDRANT_PORT"])
    NEO4J_URI: str = os.environ["NEO4J_URI"]
    NEO4J_USER: str = os.environ["NEO4J_USER"]
    NEO4J_PASSWORD: str = os.environ["NEO4J_PASSWORD"]
    DOCKER_HOST: str = os.environ["DOCKER_HOST"]
    PAYOS_API_URL: str = os.environ["PAYOS_API_URL"]
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
    LLM_MODEL: str = os.environ["LLM_MODEL"]
    QWEN_MODEL: str = os.environ["QWEN_MODEL"]
    EMBEDDING_MODEL: str = os.environ["EMBEDDING_MODEL"]
    RERANKER_MODEL: str = os.environ["RERANKER_MODEL"]
    NLLB_MODEL: str = os.environ["NLLB_MODEL"]
    NLI_MODEL_NAME: str = os.environ["NLI_MODEL_NAME"]
    DOCLING_MODEL: str = os.environ["DOCLING_MODEL"]
    PLATFORM_SYSTEM_ID: str = os.environ["PLATFORM_SYSTEM_ID"]
    MANAGEMENT_URL: str = get_service_url("MANAGEMENT")
    USAGE_URL: str = get_service_url("USAGE")
    DRM_URL: str = get_service_url("DRM")
    WEBSOCKET_URL: str = get_service_url("WEBSOCKET")
    AGENTIC_AI_DB_NAME: str = os.environ["AGENTIC_AI_DB_NAME"]
    CONTENT_URL: str = get_service_url("CONTENT")
    AGENT_FAILURE_RATE_THRESHOLD: float = float(os.environ["AGENT_FAILURE_RATE_THRESHOLD"])
    AGENT_TOOL_FAILURE_THRESHOLD: int = int(os.environ["AGENT_TOOL_FAILURE_THRESHOLD"])
    AGENT_SECURITY_VIOLATION_THRESHOLD: int = int(os.environ["AGENT_SECURITY_VIOLATION_THRESHOLD"])
    AGENT_SLOW_DURATION_MS_THRESHOLD: int = int(os.environ["AGENT_SLOW_DURATION_MS_THRESHOLD"])
    AGENT_ROUTE_CONFIDENCE_THRESHOLD: float = float(os.environ["AGENT_ROUTE_CONFIDENCE_THRESHOLD"])
    AGENT_EXECUTION_TIMEOUT_SECONDS: int = int(os.environ["AGENT_EXECUTION_TIMEOUT_SECONDS"])
    AGENT_RECURSION_LIMIT: int = int(os.environ["AGENT_RECURSION_LIMIT"])
    AGENT_MAX_CONTEXT_TOKENS: int = int(os.environ["AGENT_MAX_CONTEXT_TOKENS"])
    AGENT_HISTORY_MAX_TURNS: int = int(os.environ["AGENT_HISTORY_MAX_TURNS"])
    AGENT_DEFAULT_MAX_OUTPUT_TOKENS: int = int(os.environ["AGENT_DEFAULT_MAX_OUTPUT_TOKENS"])
    AGENT_PROACTIVE_MEMORY_ENABLED: bool = os.environ["AGENT_PROACTIVE_MEMORY_ENABLED"].lower() == "true"
    AGENT_FILE_ROOT: str = os.environ["AGENT_FILE_ROOT"]
    AGENT_ARCHIVE_MAX_FILES: int = int(os.environ["AGENT_ARCHIVE_MAX_FILES"])
    AGENT_ARCHIVE_MAX_UNCOMPRESSED_BYTES: int = int(os.environ["AGENT_ARCHIVE_MAX_UNCOMPRESSED_BYTES"])
    AGENT_ARCHIVE_MAX_COMPRESSION_RATIO: float = float(os.environ["AGENT_ARCHIVE_MAX_COMPRESSION_RATIO"])
    MCP_ALLOWED_STDIO_COMMANDS: str = os.environ["MCP_ALLOWED_STDIO_COMMANDS"]
    MCP_ALLOWED_REMOTE_HOSTS: str = os.environ["MCP_ALLOWED_REMOTE_HOSTS"]
    MCP_ALLOW_PRIVATE_NETWORKS: bool = os.environ["MCP_ALLOW_PRIVATE_NETWORKS"].lower() == "true"
    MCP_BOOTSTRAP_CONNECTORS: str = os.environ["MCP_BOOTSTRAP_CONNECTORS"]
    FINETUNE_MODELS_DIR: str = os.environ["FINETUNE_MODELS_DIR"]
    FINETUNE_ADAPTERS_DIR: str = os.environ["FINETUNE_ADAPTERS_DIR"]
    FINETUNE_GGUF_DIR: str = os.environ["FINETUNE_GGUF_DIR"]

settings = Settings()
