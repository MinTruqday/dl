from pydantic import BaseModel
import os

class Settings(BaseModel):
    REDIS_URI: str = os.getenv("REDIS_URI", "redis://redis:6379/0")
    SECRET_KEY: str = os.getenv("SECRET_KEY", "your-super-secret-key-that-should-be-very-long")
    ALGORITHM: str = "HS256"

settings = Settings()
