import os

from pydantic import BaseModel


class Settings(BaseModel):
    PROJECT_NAME: str = os.getenv("PROJECT_NAME", "DocLib")
    VERSION: str = os.getenv("VERSION", "1.0.0")
    SECRET_KEY: str = os.getenv("SECRET_KEY", "")
    CORS_ALLOWED_ORIGINS: str = os.getenv("CORS_ALLOWED_ORIGINS", "")
    MONGODB_URI: str = os.getenv("MONGODB_URI", "mongodb://mongodb:27017/doclib")
    REDIS_URI: str = os.getenv("REDIS_URI", "redis://redis:6379/0")
    CONTENT_DB_NAME: str = os.getenv("CONTENT_DB_NAME", "doclib_content")
    MESSAGING_DB_NAME: str = os.getenv("MESSAGING_DB_NAME", "doclib_messaging")
    MAX_WS_MESSAGE_BYTES: int = int(os.getenv("MAX_WS_MESSAGE_BYTES", "262144"))
    MAX_WS_FRAMES_PER_SECOND: int = int(os.getenv("MAX_WS_FRAMES_PER_SECOND", "20"))
    MAX_WS_CONNECTIONS_PER_USER: int = int(os.getenv("MAX_WS_CONNECTIONS_PER_USER", "5"))

settings = Settings()
