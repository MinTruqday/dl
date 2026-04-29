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
    MINIO_PUBLIC_URL: Optional[str] = os.getenv("MINIO_PUBLIC_URL")
    
    HYBRID_ALPHA: float = float(os.getenv("HYBRID_ALPHA"))
    ACTIVE_LLM_MODEL: str = os.getenv("LLAMA_MODEL")
    AGENTIC_RAG_URL: str = os.getenv("AGENTIC_RAG_URL")
    INTERNAL_API_URL: Optional[str] = os.getenv("INTERNAL_API_URL")
    CORE_BACKEND_URL: Optional[str] = os.getenv("CORE_BACKEND_URL")
    
    SMTP_HOST: str = os.getenv("SMTP_HOST")
    SMTP_PORT: int = int(os.getenv("SMTP_PORT"))
    SMTP_USER: Optional[str] = os.getenv("SMTP_USER")
    SMTP_PASS: Optional[str] = os.getenv("SMTP_PASS")
    
    PASSKEY_RP_ID: str = os.getenv("PASSKEY_RP_ID")
    PASSKEY_RP_NAME: str = os.getenv("PASSKEY_RP_NAME")
    PASSKEY_ALLOWED_ORIGINS: str = os.getenv("PASSKEY_ALLOWED_ORIGINS")

settings = Settings()
