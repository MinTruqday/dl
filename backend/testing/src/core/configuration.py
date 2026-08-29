import os

from pydantic import BaseModel


class Settings(BaseModel):
    PROJECT_NAME: str = os.getenv("PROJECT_NAME", "Veriq")
    VERSION: str = os.getenv("VERSION", "1.0.0")
    SECRET_KEY: str = os.getenv("SECRET_KEY", "development-only-secret")
    CORS_ALLOWED_ORIGINS: str = os.getenv("CORS_ALLOWED_ORIGINS", "http://localhost:3000")
    MONGODB_URI: str = os.getenv("MONGODB_URI", "mongodb://mongodb:27017")
    TESTING_DB_NAME: str = os.getenv("TESTING_DB_NAME", "testing")
    TESTING_ALLOW_TEST_IDENTITY: bool = os.getenv("TESTING_ALLOW_TEST_IDENTITY", "false").lower() == "true"
    PROJECT_CREATION_POLICY: str = os.getenv("PROJECT_CREATION_POLICY", "AUTHENTICATED")
    AI_URL: str = os.getenv("AI_URL", "http://ai:8000")
    CONTENT_URL: str = os.getenv("CONTENT_URL", "http://content:8000")
    WORKER_URL: str = os.getenv("WORKER_URL", "http://worker:8000")
    CLOUD_URL: str = os.getenv("CLOUD_URL", "http://cloud:8000")


settings = Settings()
