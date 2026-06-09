from pydantic import BaseModel
import os
from typing import Optional

class Settings(BaseModel):
    MONGODB_URI: str = os.getenv("MONGODB_URI")
    MONGODB_DB_NAME: str = os.getenv("MONGODB_DB_NAME")
    REDIS_URI: str = os.getenv("REDIS_URI")
    SECRET_KEY: str = os.getenv("SECRET_KEY")

    GOOGLE_CLIENT_ID: Optional[str] = os.getenv("GOOGLE_CLIENT_ID")
    GOOGLE_CLIENT_SECRET: Optional[str] = os.getenv("GOOGLE_CLIENT_SECRET")
    GOOGLE_REDIRECT_URI: Optional[str] = os.getenv("GOOGLE_REDIRECT_URI")

    SMTP_HOST: Optional[str] = os.getenv("SMTP_HOST")
    SMTP_PORT: Optional[str] = os.getenv("SMTP_PORT")
    SMTP_USER: Optional[str] = os.getenv("SMTP_USER")
    SMTP_PASS: Optional[str] = os.getenv("SMTP_PASS")
    SENDER_EMAIL: Optional[str] = os.getenv("SENDER_EMAIL")
    SENDER_NAME: Optional[str] = os.getenv("SENDER_NAME")

    PASSKEY_RP_ID: Optional[str] = os.getenv("PASSKEY_RP_ID")
    PASSKEY_RP_NAME: Optional[str] = os.getenv("PASSKEY_RP_NAME")
    PASSKEY_ALLOWED_ORIGINS: Optional[str] = os.getenv("PASSKEY_ALLOWED_ORIGINS")

    MINIO_ENDPOINT: Optional[str] = os.getenv("MINIO_ENDPOINT")
    MINIO_ACCESS_KEY: Optional[str] = os.getenv("MINIO_ACCESS_KEY")
    MINIO_SECRET_KEY: Optional[str] = os.getenv("MINIO_SECRET_KEY")
    MINIO_BUCKET_NAME: Optional[str] = os.getenv("MINIO_BUCKET_NAME")
    MINIO_REGION: Optional[str] = os.getenv("MINIO_REGION")

settings = Settings()
