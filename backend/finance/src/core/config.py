from pydantic import BaseModel
import os
from typing import Optional

class Settings(BaseModel):
    MONGODB_URI: str = os.getenv("MONGODB_URI")
    REDIS_URL: str = os.getenv("REDIS_URL")
    PAYOS_CLIENT_ID: Optional[str] = os.getenv("PAYOS_CLIENT_ID")
    PAYOS_API_KEY: Optional[str] = os.getenv("PAYOS_API_KEY")
    PAYOS_CHECKSUM_KEY: Optional[str] = os.getenv("PAYOS_CHECKSUM_KEY")
    PAYOS_RETURN_URL: Optional[str] = os.getenv("PAYOS_RETURN_URL")

settings = Settings()
