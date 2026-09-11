from pymongo import ReturnDocument

from src.core.database import database


class TestConditionRepository:
    @property
    def collection(self):
        return database.value.test_conditions

    async def create(self, value):
        await self.collection.insert_one(value)
        return value

    async def get(self, condition_id):
        return await self.collection.find_one({"_id": condition_id})

    async def list(self, query, skip, limit):
        total = await self.collection.count_documents(query)
        items = await self.collection.find(query).sort("updated_at", -1).skip(skip).limit(limit).to_list(limit)
        return items, total

    async def update(self, condition_id, project_id, revision, statuses, changes):
        return await self.collection.find_one_and_update(
            {"_id": condition_id, "project_id": project_id, "revision": revision, "status": {"$in": list(statuses)}},
            {"$set": changes, "$inc": {"revision": 1}},
            return_document=ReturnDocument.AFTER,
        )


test_condition_repository = TestConditionRepository()
