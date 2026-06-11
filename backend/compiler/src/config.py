import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    AGENTIC_AI_URL: str = os.getenv("AGENTIC_AI_URL", "http://agentic-ai:8400")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "allow"

settings = Settings()
