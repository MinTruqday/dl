from src.core.infrastructure.database import database


class MongoClient:
    def get_db(self):
        return database.mongodb

    async def find_one(self, collection: str, query: dict, projection=None, **kwargs):
        return await self.get_db()[collection].find_one(query, projection, **kwargs)

    def find(self, collection: str, query: dict, projection=None, sort=None):
        cursor = self.get_db()[collection].find(query, projection)
        return cursor.sort(sort) if sort else cursor

    async def insert_one(self, collection: str, document: dict, **kwargs):
        return await self.get_db()[collection].insert_one(document, **kwargs)

    async def insert_many(self, collection: str, documents: list):
        return await self.get_db()[collection].insert_many(documents)

    async def update_one(self, collection: str, query: dict, update: dict, upsert=False):
        return await self.get_db()[collection].update_one(query, update, upsert=upsert)

    async def update_many(self, collection: str, query: dict, update: dict, upsert=False):
        return await self.get_db()[collection].update_many(query, update, upsert=upsert)

    async def delete_one(self, collection: str, query: dict):
        return await self.get_db()[collection].delete_one(query)

    async def delete_many(self, collection: str, query: dict):
        return await self.get_db()[collection].delete_many(query)

    async def count_documents(self, collection: str, query: dict):
        return await self.get_db()[collection].count_documents(query)

    def aggregate(self, collection: str, pipeline: list):
        return self.get_db()[collection].aggregate(pipeline)


mongo = MongoClient()
