from pydantic import BaseModel
import os

class Settings(BaseModel):
    MONGODB_URI: str = os.getenv("MONGODB_URI")
    MONGODB_DB_NAME: str = os.getenv("MONGODB_DB_NAME")
    REDIS_URI: str = os.getenv("REDIS_URI")
    SECRET_KEY: str = os.getenv("SECRET_KEY")

settings = Settings()
