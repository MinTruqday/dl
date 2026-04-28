from pydantic import BaseModel
import os
from typing import Optional

class Settings(BaseModel):
    PROJECT_NAME: str = "DocLib"
    VERSION: str = "1.0.0"

    SECRET_KEY: str = os.getenv("SECRET_KEY", "doclib-password")
    CORS_ALLOWED_ORIGINS: str = os.getenv("CORS_ALLOWED_ORIGINS", "http://localhost:3000,http://localhost:3001")
    
    MONGODB_URI: str = os.getenv("MONGODB_URI", "mongodb://mongodb:27017/doclib")
    MONGODB_DB_NAME: str = os.getenv("MONGODB_DB_NAME", "doclib")
    REDIS_URI: str = os.getenv("REDIS_URI", "redis://redis:6379/0")
    RABBITMQ_URI: str = os.getenv("RABBITMQ_URI", "amqp://guest:guest@rabbitmq:5672/")
    
    GOOGLE_CLIENT_ID: Optional[str] = os.getenv("GOOGLE_CLIENT_ID")
    GOOGLE_CLIENT_SECRET: Optional[str] = os.getenv("GOOGLE_CLIENT_SECRET")
    GOOGLE_REDIRECT_URI: Optional[str] = os.getenv("GOOGLE_REDIRECT_URI")
    
    MINIO_ENDPOINT: str = os.getenv("MINIO_ENDPOINT", "http://minio:9000")
    MINIO_ACCESS_KEY: str = os.getenv("MINIO_ACCESS_KEY", "minioadmin")
    MINIO_SECRET_KEY: str = os.getenv("MINIO_SECRET_KEY", "miniopassword")
    MINIO_BUCKET_NAME: str = os.getenv("MINIO_BUCKET_NAME", "doclib-documents")
    MINIO_PUBLIC_URL: Optional[str] = os.getenv("MINIO_PUBLIC_URL")
    
    HYBRID_ALPHA: float = float(os.getenv("HYBRID_ALPHA", "0.5"))
    ACTIVE_LLM_MODEL: str = os.getenv("LLAMA_MODEL", "meta-llama/Llama-4-Maverick-17B-128E-Instruct-FP8")
    AGENTIC_RAG_URL: str = os.getenv("AGENTIC_RAG_URL", "http://agentic-rag:8100")
    
    SMTP_HOST: str = os.getenv("SMTP_HOST", "smtp@gmail.com")
    SMTP_PORT: int = int(os.getenv("SMTP_PORT", "587"))
    SMTP_USER: Optional[str] = os.getenv("SMTP_USER")
    SMTP_PASS: Optional[str] = os.getenv("SMTP_PASS")

settings = Settings()
