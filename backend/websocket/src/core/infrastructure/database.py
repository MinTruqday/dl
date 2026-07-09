from src.core.infrastructure.redis import redis
import asyncio
import os

import redis.asyncio as aioredis
from loguru import logger

from src.core.infrastructure.configuration import settings

class DatabaseInfrastructure:
    def __init__(self):
        self.mongodb = None
        self.redis = None

database = DatabaseInfrastructure()
_database_initialized = False

async def init_db():
    global _database_initialized
    if _database_initialized:
        return
        
    redis_uri = settings.REDIS_URI
    if not redis_uri:
        logger.error("Failed to initialize database connection due to missing REDIS URI")
        import sys
        sys.exit(1)

    database.redis = aioredis.from_url(redis_uri, decode_responses=True)
    _database_initialized = True
    
async def setup_indexes():
    pass

async def close_db():
    if database.mongodb:
        database.mongodb.close()
    await database.redis.close()
