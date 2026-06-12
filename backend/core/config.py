from pydantic import BaseModel
import os
from typing import Optional


class Settings(BaseModel):
    PROJECT_NAME: str = "DocLib"
    VERSION: str = "1.0.0"

    SECRET_KEY: str = os.getenv("SECRET_KEY")
    CORS_ALLOWED_ORIGINS: str = os.getenv("CORS_ALLOWED_ORIGINS")

    MONGODB_URI: str = os.getenv("MONGODB_URI")
    MONGODB_DB_NAME: str = os.getenv("MONGODB_DB_NAME")
    REDIS_URI: str = os.getenv("REDIS_URI")
    RABBITMQ_URI: str = os.getenv("RABBITMQ_URI")

    GOOGLE_CLIENT_ID: Optional[str] = os.getenv("GOOGLE_CLIENT_ID")
    GOOGLE_CLIENT_SECRET: Optional[str] = os.getenv("GOOGLE_CLIENT_SECRET")
    GOOGLE_REDIRECT_URI: Optional[str] = os.getenv("GOOGLE_REDIRECT_URI")

    MINIO_ENDPOINT: str = os.getenv("MINIO_ENDPOINT")
    MINIO_ACCESS_KEY: str = os.getenv("MINIO_ACCESS_KEY")
    MINIO_SECRET_KEY: str = os.getenv("MINIO_SECRET_KEY")
    MINIO_BUCKET_NAME: str = os.getenv("MINIO_BUCKET_NAME")
    MINIO_REGION: str = os.getenv("MINIO_REGION")
    MINIO_PUBLIC_URL: Optional[str] = os.getenv("MINIO_PUBLIC_URL")

    HF_TOKEN: str = os.getenv("HF_TOKEN")
    LLAMA_MODEL: str = os.getenv("LLAMA_MODEL")
    EMBEDDING_MODEL: str = os.getenv("EMBEDDING_MODEL")
    RERANKER_MODEL: str = os.getenv("RERANKER_MODEL")
    NLLB_MODEL: str = os.getenv("NLLB_MODEL")
    NLI_MODEL_NAME: str = os.getenv("NLI_MODEL_NAME")
    IMAGE_GEN_MODEL: str = os.getenv("IMAGE_GEN_MODEL")

    HYBRID_ALPHA: float = float(os.getenv("HYBRID_ALPHA", "0.5"))
    EMBEDDING_DIMENSIONS: int = int(os.getenv("EMBEDDING_DIMENSIONS", "384"))
    EMBEDDING_BATCH_SIZE: int = int(os.getenv("EMBEDDING_BATCH_SIZE", "32"))
    MEMORY_MAX_TURNS: int = int(os.getenv("MEMORY_MAX_TURNS", "10"))

    TAVILY_API_KEY: Optional[str] = os.getenv("TAVILY_API_KEY")

    QDRANT_URL: str = os.getenv("QDRANT_URL")
    QDRANT_HOST: str = os.getenv("QDRANT_HOST")
    QDRANT_PORT: int = int(os.getenv("QDRANT_PORT", "6333"))

    AGENTIC_AI_URL: str = os.getenv("AGENTIC_AI_URL")
    INTERNAL_API_URL: str = os.getenv("INTERNAL_API_URL")
    CORE_BACKEND_URL: Optional[str] = os.getenv("CORE_BACKEND_URL")
    COMPILER_URL: str = os.getenv("COMPILER_URL")
    COLLECTOR_URL: str = os.getenv("COLLECTOR_URL")
    CONTACT_URL: str = os.getenv("CONTACT_URL")
    FINANCE_URL: str = os.getenv("FINANCE_URL")
    SIGNAL_URL: str = os.getenv("SIGNAL_URL")
    PROVISION_URL: str = os.getenv("PROVISION_URL", "http://provision:8450")
    FLARESOLVERR_URL: str = os.getenv("FLARESOLVERR_URL", "http://flaresolverr:8191/v1")

    SMTP_HOST: str = os.getenv("SMTP_HOST")
    SMTP_PORT: int = int(os.getenv("SMTP_PORT", "587"))
    SMTP_USER: Optional[str] = os.getenv("SMTP_USER")
    SMTP_PASS: Optional[str] = os.getenv("SMTP_PASS")
    SENDER_EMAIL: Optional[str] = os.getenv("SENDER_EMAIL")
    SENDER_NAME: Optional[str] = os.getenv("SENDER_NAME")

    PASSKEY_RP_ID: str = os.getenv("PASSKEY_RP_ID")
    PASSKEY_RP_NAME: str = os.getenv("PASSKEY_RP_NAME")
    PASSKEY_ALLOWED_ORIGINS: str = os.getenv("PASSKEY_ALLOWED_ORIGINS")

    PLATFORM_ADMIN_ID: str = os.getenv("PLATFORM_ADMIN_ID")

    OLLAMA_BASE_URL: str = os.getenv("OLLAMA_BASE_URL")
    OLLAMA_MODEL: str = os.getenv("OLLAMA_MODEL")
    PAYOS_CLIENT_ID: str = os.getenv("PAYOS_CLIENT_ID")
    PAYOS_API_KEY: str = os.getenv("PAYOS_API_KEY")
    PAYOS_CHECKSUM_KEY: str = os.getenv("PAYOS_CHECKSUM_KEY")
    PAYOS_RETURN_URL: str = os.getenv("PAYOS_RETURN_URL")


settings = Settings()
