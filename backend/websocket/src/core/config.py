from pydantic import BaseModel
import os

class Settings(BaseModel):
    REDIS_URI: str = os.getenv("REDIS_URI")
    SECRET_KEY: str = os.getenv("SECRET_KEY")
    ALGORITHM: str = "HS256"

settings = Settings()
