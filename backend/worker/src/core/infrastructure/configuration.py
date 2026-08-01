import os

from pydantic import BaseModel


def get_service_url(service_name: str) -> str:
    host = os.getenv(f"{service_name}_SERVICE_HOST")
    port = os.getenv(f"{service_name}_SERVICE_PORT", "80")
    return f"http://{host}:{port}" if host else f"http://{service_name.lower()}:8000"


class Settings(BaseModel):
    PROJECT_NAME: str = os.environ["PROJECT_NAME"]
    VERSION: str = os.environ["VERSION"]
    SECRET_KEY: str = os.environ["SECRET_KEY"]
    MONGODB_URI: str = os.environ["MONGODB_URI"]
    RABBITMQ_URI: str = os.environ["RABBITMQ_URI"]
    WORKER_DB_NAME: str = os.environ["WORKER_DB_NAME"]
    MINIO_ENDPOINT: str = os.environ["MINIO_ENDPOINT"]
    MINIO_ACCESS_KEY: str = os.environ["MINIO_ACCESS_KEY"]
    MINIO_SECRET_KEY: str = os.environ["MINIO_SECRET_KEY"]
    MINIO_PRIVATE_BUCKET: str = os.environ["MINIO_PRIVATE_BUCKET"]
    MAX_COMPILE_INPUT_BYTES: int = int(os.environ["MAX_COMPILE_INPUT_BYTES"])
    MAX_COMPILE_OUTPUT_BYTES: int = int(os.environ["MAX_COMPILE_OUTPUT_BYTES"])
    WORKER_MAX_RETRIES: int = int(os.environ["WORKER_MAX_RETRIES"])
    CONTENT_URL: str = get_service_url("CONTENT")


settings = Settings()
