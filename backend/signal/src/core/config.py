from pydantic import BaseModel
import os
from typing import Optional

class Settings(BaseModel):
    MONGODB_URI: str = os.getenv("MONGODB_URI")
    MONGODB_DB_NAME: str = os.getenv("MONGODB_DB_NAME")
    REDIS_URI: str = os.getenv("REDIS_URI")
    SECRET_KEY: str = os.getenv("SECRET_KEY")

    SMTP_HOST: Optional[str] = os.getenv("SMTP_HOST")
    SMTP_PORT: Optional[str] = os.getenv("SMTP_PORT")
    SMTP_USER: Optional[str] = os.getenv("SMTP_USER")
    SMTP_PASS: Optional[str] = os.getenv("SMTP_PASS")
    SENDER_EMAIL: Optional[str] = os.getenv("SENDER_EMAIL")
    SENDER_NAME: Optional[str] = os.getenv("SENDER_NAME")

settings = Settings()
