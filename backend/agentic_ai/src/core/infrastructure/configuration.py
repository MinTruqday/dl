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
        return f"http://{k8s_host}:8000"
    return f"http://{service_name_underscore.lower()}:8000"


def get_runtime_path(*parts: str) -> str:
    return os.path.join(tempfile.gettempdir(), *parts)


class Settings(BaseModel):
    PROJECT_NAME: str = os.getenv("PROJECT_NAME", "DocLib")
    VERSION: str = os.getenv("VERSION", "1.0.0")
    INTERNAL_API_URL: str = os.getenv("INTERNAL_API_URL", "http://traefik:8000")
    SECRET_KEY: str = os.getenv("SECRET_KEY", "")
    CORS_ALLOWED_ORIGINS: str = os.getenv("CORS_ALLOWED_ORIGINS", "")
    MONGODB_URI: str = os.getenv("MONGODB_URI", "mongodb://mongodb:27017/doclib")
    REDIS_URI: str = os.getenv("REDIS_URI", "redis://redis:6379/0")
    RABBITMQ_URI: str = os.getenv("RABBITMQ_URI", "amqp://guest:guest@rabbitmq:5672/")
    QDRANT_URL: str = os.getenv("QDRANT_URL", "http://qdrant:6333")
    QDRANT_HOST: str = os.getenv("QDRANT_HOST", "qdrant")
    QDRANT_PORT: int = int(os.getenv("QDRANT_PORT", "6333"))
    NEO4J_URI: str = os.getenv("NEO4J_URI", "bolt://neo4j:7687")
    NEO4J_USER: str = os.getenv("NEO4J_USER", "neo4j")
    NEO4J_PASSWORD: str = os.getenv("NEO4J_PASSWORD", "password")
    DOCKER_HOST: str = os.getenv("DOCKER_HOST", "unix://var/run/docker.sock")
    PAYOS_API_URL: str = os.getenv("PAYOS_API_URL", "")
    MINIO_ENDPOINT: str = os.getenv("MINIO_ENDPOINT", "minio:9000")
    MINIO_ACCESS_KEY: str = os.getenv("MINIO_ACCESS_KEY", "")
    MINIO_SECRET_KEY: str = os.getenv("MINIO_SECRET_KEY", "")
    MINIO_PRIVATE_BUCKET: str = os.getenv("MINIO_PRIVATE_BUCKET", "doclib-private")
    MINIO_PUBLIC_BUCKET: str = os.getenv("MINIO_PUBLIC_BUCKET", "doclib-public")
    MINIO_REGION: str = os.getenv("MINIO_REGION", "us-east-1")
    MINIO_PUBLIC_URL: Optional[str] = os.getenv("MINIO_PUBLIC_URL")
    MIN_FILE_SIZE_BYTES: int = int(os.getenv("MIN_FILE_SIZE_BYTES", "5000"))
    TAVILY_API_KEY: Optional[str] = os.getenv("TAVILY_API_KEY")
    HF_TOKEN: str = os.getenv("HF_TOKEN", "")
    LLM_MODEL: str = os.getenv("LLM_MODEL", "Qwen/Qwen3.6-27B")
    QWEN_MODEL: str = os.getenv("QWEN_MODEL", "Qwen/Qwen3.6-35B-A3B")
    EMBEDDING_MODEL: str = os.getenv("EMBEDDING_MODEL", "BAAI/bge-m3")
    RERANKER_MODEL: str = os.getenv("RERANKER_MODEL", "BAAI/bge-reranker-v2-m3")
    NLLB_MODEL: str = os.getenv("NLLB_MODEL", "facebook/nllb-200-distilled-600M")
    NLI_MODEL_NAME: str = os.getenv("NLI_MODEL_NAME", "cross-encoder/nli-deberta-v3-base")
    DOCLING_MODEL: str = os.getenv("DOCLING_MODEL", "ds4sd/docling-models")
    PLATFORM_SYSTEM_ID: str = os.getenv("PLATFORM_SYSTEM_ID", "")
    MANAGEMENT_URL: str = get_service_url("MANAGEMENT")
    USAGE_URL: str = get_service_url("USAGE")
    DRM_URL: str = get_service_url("DRM")
    WEBSOCKET_URL: str = get_service_url("WEBSOCKET")
    AGENTIC_AI_DB_NAME: str = os.getenv("AGENTIC_AI_DB_NAME", "doclib_agentic_ai")
    AGENT_FAILURE_RATE_THRESHOLD: float = float(os.getenv("AGENT_FAILURE_RATE_THRESHOLD", "0.15"))
    AGENT_TOOL_FAILURE_THRESHOLD: int = int(os.getenv("AGENT_TOOL_FAILURE_THRESHOLD", "3"))
    AGENT_SECURITY_VIOLATION_THRESHOLD: int = int(os.getenv("AGENT_SECURITY_VIOLATION_THRESHOLD", "5"))
    AGENT_SLOW_DURATION_MS_THRESHOLD: int = int(os.getenv("AGENT_SLOW_DURATION_MS_THRESHOLD", "30000"))
    AGENT_ROUTE_CONFIDENCE_THRESHOLD: float = float(os.getenv("AGENT_ROUTE_CONFIDENCE_THRESHOLD", "0.55"))
    AGENT_EXECUTION_TIMEOUT_SECONDS: int = int(os.getenv("AGENT_EXECUTION_TIMEOUT_SECONDS", "900"))
    AGENT_RECURSION_LIMIT: int = int(os.getenv("AGENT_RECURSION_LIMIT", "200"))
    AGENT_MAX_CONTEXT_TOKENS: int = int(os.getenv("AGENT_MAX_CONTEXT_TOKENS", "32768"))
    AGENT_HISTORY_MAX_TURNS: int = int(os.getenv("AGENT_HISTORY_MAX_TURNS", "50"))
    AGENT_DEFAULT_MAX_OUTPUT_TOKENS: int = int(os.getenv("AGENT_DEFAULT_MAX_OUTPUT_TOKENS", "4096"))
    AGENT_PROACTIVE_MEMORY_ENABLED: bool = os.getenv("AGENT_PROACTIVE_MEMORY_ENABLED", "true").lower() == "true"
    AGENT_FILE_ROOT: str = os.getenv("AGENT_FILE_ROOT", get_runtime_path("doclib_agent_files"))
    AGENT_ARCHIVE_MAX_FILES: int = int(os.getenv("AGENT_ARCHIVE_MAX_FILES", "1000"))
    AGENT_ARCHIVE_MAX_UNCOMPRESSED_BYTES: int = int(os.getenv("AGENT_ARCHIVE_MAX_UNCOMPRESSED_BYTES", "536870912"))
    AGENT_ARCHIVE_MAX_COMPRESSION_RATIO: float = float(os.getenv("AGENT_ARCHIVE_MAX_COMPRESSION_RATIO", "100"))
    MCP_ALLOWED_STDIO_COMMANDS: str = os.getenv("MCP_ALLOWED_STDIO_COMMANDS", "")
    MCP_ALLOWED_SSE_HOSTS: str = os.getenv("MCP_ALLOWED_SSE_HOSTS", "")
    FINETUNE_MODELS_DIR: str = os.getenv("FINETUNE_MODELS_DIR", get_runtime_path("doclib_finetune", "models"))
    FINETUNE_ADAPTERS_DIR: str = os.getenv("FINETUNE_ADAPTERS_DIR", get_runtime_path("doclib_finetune", "adapters"))
    FINETUNE_GGUF_DIR: str = os.getenv("FINETUNE_GGUF_DIR", get_runtime_path("doclib_finetune", "gguf"))

settings = Settings()
