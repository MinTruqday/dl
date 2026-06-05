from pydantic import BaseModel
import os
from typing import Optional


class Settings(BaseModel):
    PROJECT_NAME: str = "DocLib"

    MONGODB_URI: str = os.getenv("MONGODB_URI")
    REDIS_URI: str = os.getenv("REDIS_URI")

    HF_TOKEN: str = os.getenv("HF_TOKEN")
    LLAMA_MODEL: str = os.getenv("LLAMA_MODEL")
    EMBEDDING_MODEL: str = os.getenv("EMBEDDING_MODEL")
    RERANKER_MODEL: str = os.getenv("RERANKER_MODEL")
    NLLB_MODEL: str = os.getenv("NLLB_MODEL")
    NLI_MODEL_NAME: str = os.getenv("NLI_MODEL_NAME")
    IMAGE_GEN_MODEL: str = os.getenv("IMAGE_GEN_MODEL")

    EMBEDDING_DIMENSIONS: int = int(os.getenv("EMBEDDING_DIMENSIONS"))
    EMBEDDING_BATCH_SIZE: int = int(os.getenv("EMBEDDING_BATCH_SIZE"))
    MEMORY_MAX_TURNS: int = int(os.getenv("MEMORY_MAX_TURNS"))

    TAVILY_API_KEY: Optional[str] = os.getenv("TAVILY_API_KEY")
    LANGCHAIN_API_KEY: Optional[str] = os.getenv("LANGCHAIN_API_KEY")
    LANGCHAIN_TRACING_V2: Optional[str] = os.getenv("LANGCHAIN_TRACING_V2")
    LANGCHAIN_PROJECT: Optional[str] = os.getenv("LANGCHAIN_PROJECT")

    MINIO_ENDPOINT: str = os.getenv("MINIO_ENDPOINT")
    MINIO_ACCESS_KEY: str = os.getenv("MINIO_ACCESS_KEY")
    MINIO_SECRET_KEY: str = os.getenv("MINIO_SECRET_KEY")
    MINIO_BUCKET_NAME: str = os.getenv("MINIO_BUCKET_NAME")
    MINIO_REGION: str = os.getenv("MINIO_REGION")

    QDRANT_URL: str = os.getenv("QDRANT_URL")
    QDRANT_HOST: str = os.getenv("QDRANT_HOST")
    QDRANT_PORT: int = int(os.getenv("QDRANT_PORT"))

    AGENTIC_AI_URL: str = os.getenv("AGENTIC_AI_URL")
    INTERNAL_API_URL: str = os.getenv("INTERNAL_API_URL")
    CORE_BACKEND_URL: Optional[str] = os.getenv("CORE_BACKEND_URL")

    OLLAMA_BASE_URL: str = os.getenv("OLLAMA_BASE_URL")
    OLLAMA_MODEL: str = os.getenv("OLLAMA_MODEL")

settings = Settings()

if settings.LANGCHAIN_API_KEY:
    os.environ["LANGCHAIN_TRACING_V2"] = settings.LANGCHAIN_TRACING_V2 or "true"
    os.environ["LANGCHAIN_PROJECT"] = settings.LANGCHAIN_PROJECT or "DocLib-Agent"
    os.environ["LANGCHAIN_API_KEY"] = settings.LANGCHAIN_API_KEY
