from src.core.infrastructure.configuration import settings

class DatabaseInfrastructure:
    def __init__(self):
        self.mongodb = None
        self.redis = None

database = DatabaseInfrastructure()

async def init_db():
    if not settings.SECRET_KEY:
        raise RuntimeError("SECRET_KEY is required")
    from motor.motor_asyncio import AsyncIOMotorClient
    import redis.asyncio as aioredis
    database.mongodb = AsyncIOMotorClient(settings.MONGODB_URI)
    await database.mongodb.admin.command("ping")
    database.redis = aioredis.from_url(settings.REDIS_URI, decode_responses=True)
    await database.redis.ping()

async def close_db():
    if database.mongodb:
        database.mongodb.close()
        database.mongodb = None
    if database.redis:
        await database.redis.aclose()
        database.redis = None
