import os

class Settings:
    VERSION = "1.0.0"
    REDIS_URI = os.getenv("REDIS_URI", "redis://doclib_redis:6379/0")

    MONGO_URL: str = os.getenv("MONGO_URL", "http://doclib_database:8800/co-so-du-lieu")
    QUEUE_URL: str = os.getenv("QUEUE_URL", "http://doclib_queue:8802/hang-doi")
    CACHE_URL: str = os.getenv("CACHE_URL", "http://doclib_cache:8801")

settings = Settings()
