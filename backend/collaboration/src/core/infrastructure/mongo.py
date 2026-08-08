from src.core.infrastructure.configuration import settings
from src.core.infrastructure.database import database

class MongoClient:
    def __init__(self):
        self.db_name = settings.COLLABORATION_DB_NAME

    def get_db(self, db_name: str | None = None):
        if not database.mongodb:
            raise Exception("MongoDB is not initialized")
        target_db = db_name or self.db_name
        return database.mongodb[target_db]

    def get_content_db(self):
        return self.get_db(settings.CONTENT_DB_NAME)

    async def find_one(self, collection: str, query: dict, projection: dict = None, db_name: str | None = None, **kwargs):
        return await self.get_db(db_name)[collection].find_one(query, projection, **kwargs)

    def find(self, collection: str, query: dict, projection: dict = None, sort=None, skip: int = 0, limit: int = 0, db_name: str | None = None):
        cursor = self.get_db(db_name)[collection].find(query, projection)
        if sort:
            cursor = cursor.sort(sort)
        if skip:
            cursor = cursor.skip(skip)
        if limit:
            cursor = cursor.limit(limit)
        return cursor

    def aggregate(self, collection: str, pipeline: list, db_name: str | None = None):
        cursor = self.get_db(db_name)[collection].aggregate(pipeline)
        return cursor

    async def insert_one(self, collection: str, document: dict, db_name: str | None = None, **kwargs):
        return await self.get_db(db_name)[collection].insert_one(document, **kwargs)

    async def insert_many(self, collection: str, documents: list, db_name: str | None = None):
        return await self.get_db(db_name)[collection].insert_many(documents)

    async def update_one(self, collection: str, filter: dict, update: dict, upsert: bool = False, db_name: str | None = None, **kwargs):
        return await self.get_db(db_name)[collection].update_one(filter, update, upsert=upsert, **kwargs)

    async def update_many(self, collection: str, filter: dict, update: dict, upsert: bool = False, db_name: str | None = None):
        return await self.get_db(db_name)[collection].update_many(filter, update, upsert=upsert)

    async def delete_one(self, collection: str, filter: dict, db_name: str | None = None):
        return await self.get_db(db_name)[collection].delete_one(filter)

    async def delete_many(self, collection: str, filter: dict, db_name: str | None = None):
        return await self.get_db(db_name)[collection].delete_many(filter)

    async def count_documents(self, collection: str, filter: dict | None = None, db_name: str | None = None):
        return await self.get_db(db_name)[collection].count_documents(filter or {})

mongo = MongoClient()
