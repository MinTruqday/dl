from pydantic import BaseModel
import os
from typing import Optional

class Settings(BaseModel):
    MONGODB_URI: str = os.getenv("MONGODB_URI")
    MONGODB_DB_NAME: str = os.getenv("MONGODB_DB_NAME")
    REDIS_URI: str = os.getenv("REDIS_URI")
    SECRET_KEY: str = os.getenv("SECRET_KEY")

    MINIO_ENDPOINT: Optional[str] = os.getenv("MINIO_ENDPOINT")
    MINIO_ACCESS_KEY: Optional[str] = os.getenv("MINIO_ACCESS_KEY")
    MINIO_SECRET_KEY: Optional[str] = os.getenv("MINIO_SECRET_KEY")
    MINIO_BUCKET_NAME: Optional[str] = os.getenv("MINIO_BUCKET_NAME")
    MINIO_REGION: Optional[str] = os.getenv("MINIO_REGION")

    RABBITMQ_URL: Optional[str] = os.getenv("RABBITMQ_URL")

    AGENTIC_AI_URL: Optional[str] = os.getenv("AGENTIC_AI_URL")
    COMPILER_SERVICE_URL: Optional[str] = os.getenv("COMPILER_SERVICE_URL")

settings = Settings()
