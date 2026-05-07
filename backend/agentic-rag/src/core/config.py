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
    ADE_MODEL: str = os.getenv("ADE_MODEL")
    IMAGE_GEN_MODEL: str = os.getenv("IMAGE_GEN_MODEL")
    VISION_AGENT_API_KEY: Optional[str] = os.getenv("VISION_AGENT_API_KEY")
    
    EMBEDDING_DIMENSIONS: int = int(os.getenv("EMBEDDING_DIMENSIONS", "1024"))
    EMBEDDING_BATCH_SIZE: int = int(os.getenv("EMBEDDING_BATCH_SIZE", "32"))
    MEMORY_MAX_TURNS: int = int(os.getenv("MEMORY_MAX_TURNS", "10"))
    
    TAVILY_API_KEY: Optional[str] = os.getenv("TAVILY_API_KEY")
    
    MINIO_ENDPOINT: str = os.getenv("MINIO_ENDPOINT")
    MINIO_ACCESS_KEY: str = os.getenv("MINIO_ACCESS_KEY")
    MINIO_SECRET_KEY: str = os.getenv("MINIO_SECRET_KEY")
    MINIO_BUCKET_NAME: str = os.getenv("MINIO_BUCKET_NAME")
    MINIO_REGION: str = os.getenv("MINIO_REGION", "us-east-1")
    
    QDRANT_URL: str = os.getenv("QDRANT_URL")
    QDRANT_HOST: str = os.getenv("QDRANT_HOST")
    QDRANT_PORT: int = int(os.getenv("QDRANT_PORT", "6333"))
    
    INTERNAL_API_URL: str = os.getenv("INTERNAL_API_URL")
    CORE_BACKEND_URL: Optional[str] = os.getenv("CORE_BACKEND_URL")
    AGENTIC_RAG_URL: str = os.getenv("AGENTIC_RAG_URL")

settings = Settings()
