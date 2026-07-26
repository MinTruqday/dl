from datetime import datetime, timezone

from src.core.infrastructure.configuration import settings


class DatabaseInfrastructure:
    def __init__(self):
        self.mongodb = None


database = DatabaseInfrastructure()


async def init_db():
    if not settings.SECRET_KEY:
        raise RuntimeError("SECRET_KEY is required")
    from motor.motor_asyncio import AsyncIOMotorClient
    database.mongodb = AsyncIOMotorClient(settings.MONGODB_URI)
    await database.mongodb.admin.command("ping")
    jobs = database.mongodb[settings.WORKER_DB_NAME].worker_jobs
    await jobs.create_index([("document_id", 1), ("created_at", -1)])
    await jobs.create_index("expire_at", expireAfterSeconds=0)


async def close_db():
    if database.mongodb:
        database.mongodb.close()
        database.mongodb = None


async def record_job(job_id: str, values: dict, insert: dict | None = None):
    now = datetime.now(timezone.utc)
    update = {"$set": {**values, "updated_at": now}}
    if insert is not None:
        update["$setOnInsert"] = {
            "_id": job_id,
            "created_at": now,
            **insert,
        }
    await database.mongodb[settings.WORKER_DB_NAME].worker_jobs.update_one(
        {"_id": job_id},
        update,
        upsert=insert is not None,
    )
