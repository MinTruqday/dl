import os
from pydantic import BaseModel

class Settings(BaseModel):
    PROJECT_NAME: str = os.environ["PROJECT_NAME"]
    VERSION: str = os.environ["VERSION"]
    INTERNAL_API_URL: str = os.environ["INTERNAL_API_URL"]
    SECRET_KEY: str = os.environ["SECRET_KEY"]
    CORS_ALLOWED_ORIGINS: str = os.environ["CORS_ALLOWED_ORIGINS"]
    MONGODB_URI: str = os.environ["MONGODB_URI"]
    REDIS_URI: str = os.environ["REDIS_URI"]
    PLATFORM_SYSTEM_ID: str = os.environ["PLATFORM_SYSTEM_ID"]
    ASSESSMENT_URL: str = os.getenv("ASSESSMENT_URL", "http://assessment:8000")

settings = Settings()
