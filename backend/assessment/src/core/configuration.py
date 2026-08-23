import os

from pydantic import BaseModel


class Settings(BaseModel):
    PROJECT_NAME: str = os.getenv("PROJECT_NAME", "Assessment Platform")
    VERSION: str = os.getenv("VERSION", "1.0.0")
    SECRET_KEY: str = os.getenv("SECRET_KEY", "development-only-secret")
    CORS_ALLOWED_ORIGINS: str = os.getenv("CORS_ALLOWED_ORIGINS", "http://localhost:3000")
    MONGODB_URI: str = os.getenv("MONGODB_URI", "mongodb://mongodb:27017")
    REDIS_URI: str = os.getenv("REDIS_URI", "redis://redis:6379/0")
    ASSESSMENT_DB_NAME: str = os.getenv("ASSESSMENT_DB_NAME", "assessment")
    ASSESSMENT_ALLOW_TEST_IDENTITY: bool = os.getenv("ASSESSMENT_ALLOW_TEST_IDENTITY", "false").lower() == "true"
    CALIBRATION_MIN_SAMPLE_SIZE: int = int(os.getenv("CALIBRATION_MIN_SAMPLE_SIZE", "20"))
    ASSESSMENT_PII_RETENTION_DAYS: int = int(os.getenv("ASSESSMENT_PII_RETENTION_DAYS", "730"))
    WORKER_URL: str = os.getenv("WORKER_URL", "http://worker:8000")
    RAG_URL: str = os.getenv("RAG_URL", "http://rag:8000")
    AGENTIC_AI_URL: str = os.getenv("AGENTIC_AI_URL", "http://agentic_ai:8000")
    CONTENT_URL: str = os.getenv("CONTENT_URL", "http://content:8000")
    AUTHENTICATION_URL: str = os.getenv("AUTHENTICATION_URL", "http://authentication:8000")
    CLOUD_URL: str = os.getenv("CLOUD_URL", "http://cloud:8000")
    COLLECTION_URL: str = os.getenv("COLLECTION_URL", "http://collection:8000")
    COMPILATION_URL: str = os.getenv("COMPILATION_URL", "http://compilation:8000")


settings = Settings()
