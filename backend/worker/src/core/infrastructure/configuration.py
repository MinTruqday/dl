import os

from pydantic import BaseModel


class Settings(BaseModel):
    PROJECT_NAME: str = os.getenv("PROJECT_NAME", "DocLib")
    VERSION: str = os.getenv("VERSION", "1.0.0")
    SECRET_KEY: str = os.getenv("SECRET_KEY", "")
    MONGODB_URI: str = os.getenv("MONGODB_URI", "mongodb://mongodb:27017/doclib")
    RABBITMQ_URI: str = os.getenv("RABBITMQ_URI", "amqp://guest:guest@rabbitmq:5672/")
    CONTENT_DB_NAME: str = os.getenv("CONTENT_DB_NAME", "doclib_content")
    WORKER_DB_NAME: str = os.getenv("WORKER_DB_NAME", "doclib_worker")
    MINIO_ENDPOINT: str = os.getenv("MINIO_ENDPOINT", "http://minio:9000")
    MINIO_ACCESS_KEY: str = os.getenv("MINIO_ACCESS_KEY", "")
    MINIO_SECRET_KEY: str = os.getenv("MINIO_SECRET_KEY", "")
    MINIO_PRIVATE_BUCKET: str = os.getenv("MINIO_PRIVATE_BUCKET", "doclib-private")
    MAX_COMPILE_INPUT_BYTES: int = int(os.getenv("MAX_COMPILE_INPUT_BYTES", str(2 * 1024 * 1024)))
    MAX_COMPILE_OUTPUT_BYTES: int = int(os.getenv("MAX_COMPILE_OUTPUT_BYTES", str(50 * 1024 * 1024)))
    WORKER_MAX_RETRIES: int = int(os.getenv("WORKER_MAX_RETRIES", "3"))


settings = Settings()
