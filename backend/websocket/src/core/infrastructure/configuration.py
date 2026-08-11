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
    CORS_ALLOWED_ORIGINS: str = os.environ["CORS_ALLOWED_ORIGINS"]
    MONGODB_URI: str = os.environ["MONGODB_URI"]
    REDIS_URI: str = os.environ["REDIS_URI"]
    MAX_WS_MESSAGE_BYTES: int = int(os.environ["MAX_WS_MESSAGE_BYTES"])
    MAX_WS_FRAMES_PER_SECOND: int = int(os.environ["MAX_WS_FRAMES_PER_SECOND"])
    MAX_WS_CONNECTIONS_PER_USER: int = int(os.environ["MAX_WS_CONNECTIONS_PER_USER"])
    CONTENT_URL: str = get_service_url("CONTENT")

settings = Settings()
