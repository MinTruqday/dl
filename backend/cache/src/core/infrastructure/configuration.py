import os

class Settings:
    VERSION = "1.0.0"
    REDIS_URI = os.getenv("REDIS_URI", "redis://doclib_redis:6379/0")

settings = Settings()
