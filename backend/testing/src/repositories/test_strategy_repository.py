from pymongo import ReturnDocument

from src.core.database import database


class TestStrategyRepository:
    @property
    def collection(self):
        return database.value.test_strategies

    async def create(self, value):
        await self.collection.insert_one(value)
        return value

    async def get(self, strategy_id, project_id=None):
        query = {"_id": strategy_id}
        if project_id:
            query["project_id"] = project_id
        return await self.collection.find_one(query)

    async def list(self, query, skip, limit):
        total = await self.collection.count_documents(query)
        items = await self.collection.find(query).sort([("key", 1), ("version", -1)]).skip(skip).limit(limit).to_list(limit)
        return items, total

    async def update(self, strategy_id, project_id, revision, statuses, changes):
        return await self.collection.find_one_and_update(
            {"_id": strategy_id, "project_id": project_id, "revision": revision, "status": {"$in": list(statuses)}},
            {"$set": changes, "$inc": {"revision": 1}},
            return_document=ReturnDocument.AFTER,
        )

    async def active_approved(self, project_id, exclude_id=None):
        query = {"project_id": project_id, "status": "APPROVED", "active_approved": True}
        if exclude_id:
            query["_id"] = {"$ne": exclude_id}
        return await self.collection.find_one(query)

    async def next_version(self, lineage_id):
        latest = await self.collection.find_one({"lineage_id": lineage_id}, sort=[("version", -1)])
        return int(latest.get("version", 0)) + 1 if latest else 1


test_strategy_repository = TestStrategyRepository()
