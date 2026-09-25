import os

from pydantic import BaseModel


class Settings(BaseModel):
    PROJECT_NAME: str = os.environ["PROJECT_NAME"]
    VERSION: str = os.environ["VERSION"]
    SECRET_KEY: str = os.environ["SECRET_KEY"]
    CORS_ALLOWED_ORIGINS: str = os.environ["CORS_ALLOWED_ORIGINS"]
    INTERNAL_REQUEST_TIMEOUT_SECONDS: float = float(
        os.environ["INTERNAL_REQUEST_TIMEOUT_SECONDS"]
    )
    INTERNAL_LONG_REQUEST_TIMEOUT_SECONDS: float = float(
        os.environ["INTERNAL_LONG_REQUEST_TIMEOUT_SECONDS"]
    )
    MONGODB_URI: str = os.environ["MONGODB_URI"]
    TESTING_DB_NAME: str = os.environ["TESTING_DB_NAME"]
    AUTHENTICATION_URL: str = os.environ["AUTHENTICATION_URL"]
    AI_URL: str = os.environ["AI_URL"]
    AI_REQUEST_TIMEOUT_SECONDS: float = float(os.environ["AI_REQUEST_TIMEOUT_SECONDS"])
    CONTENT_URL: str = os.environ["CONTENT_URL"]
    WORKER_URL: str = os.environ["WORKER_URL"]
    CLOUD_URL: str = os.environ["CLOUD_URL"]
    MAX_REQUIREMENT_UPLOAD_SIZE_BYTES: int = int(
        os.environ["MAX_REQUIREMENT_UPLOAD_SIZE_BYTES"]
    )
    MAX_API_ARTIFACT_UPLOAD_SIZE_BYTES: int = int(
        os.environ["MAX_API_ARTIFACT_UPLOAD_SIZE_BYTES"]
    )


settings = Settings()
