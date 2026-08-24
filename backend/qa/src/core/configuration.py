import os

from pydantic import BaseModel


class Settings(BaseModel):
    PROJECT_NAME: str = os.getenv("PROJECT_NAME", "QA Workspace")
    VERSION: str = os.getenv("VERSION", "1.0.0")
    SECRET_KEY: str = os.getenv("SECRET_KEY", "development-only-secret")
    CORS_ALLOWED_ORIGINS: str = os.getenv("CORS_ALLOWED_ORIGINS", "http://localhost:3000")
    MONGODB_URI: str = os.getenv("MONGODB_URI", "mongodb://mongodb:27017")
    QA_DB_NAME: str = os.getenv("QA_DB_NAME", "qa")
    QA_ALLOW_TEST_IDENTITY: bool = os.getenv("QA_ALLOW_TEST_IDENTITY", "false").lower() == "true"
    AI_URL: str = os.getenv("AI_URL", "http://ai:8000")
    RAG_URL: str = os.getenv("RAG_URL", "http://rag:8000")
    QDRANT_URL: str = os.getenv("QDRANT_URL", "http://qdrant:6333")
    CONTENT_URL: str = os.getenv("CONTENT_URL", "http://content:8000")
    WORKER_URL: str = os.getenv("WORKER_URL", "http://worker:8000")


settings = Settings()
