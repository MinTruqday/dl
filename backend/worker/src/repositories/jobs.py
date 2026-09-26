from datetime import datetime, timezone

from pymongo import ReturnDocument

from src.core.infrastructure.configuration import settings
from src.core.infrastructure.database import database


class WorkerJobRepository:
    @property
    def collection(self):
        return database.mongodb[settings.WORKER_DB_NAME].worker_jobs

    async def record(self, job_id, values, insert=None):
        now = datetime.now(timezone.utc)
        update = {"$set": {**values, "updated_at": now}}
        if insert is not None:
            update["$setOnInsert"] = {"_id": job_id, "created_at": now, **insert}
        await self.collection.update_one({"_id": job_id}, update, upsert=insert is not None)

    async def find_one(self, query, projection=None):
        return await self.collection.find_one(query, projection)

    async def list(self, query, limit):
        return await self.collection.find(query, {"request.internal_token": 0}).sort(
            "updated_at", -1
        ).limit(limit).to_list(limit)

    async def count(self, query):
        return await self.collection.count_documents(query)

    async def overview(self, query):
        return await self.collection.aggregate(
            [{"$match": query}, {"$group": {"_id": "$status", "count": {"$sum": 1}}}]
        ).to_list(100)

    async def discard(self, job_id, values):
        return await self.collection.find_one_and_update(
            {"_id": job_id, "status": "failed"},
            {"$set": values},
            return_document=ReturnDocument.AFTER,
        )


worker_job_repository = WorkerJobRepository()
