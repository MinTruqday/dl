from src.core.infrastructure.mongo import mongo
from src.core.infrastructure.configuration import settings

class ReadingRepository:
    @classmethod
    async def update_history(cls, *args, **kwargs):
        return await mongo.update_one("reading_history", *args, **kwargs)

    @classmethod
    async def delete_historys(cls, *args, **kwargs):
        return await mongo.delete_many("reading_history", *args, **kwargs)

    @classmethod
    async def delete_history(cls, *args, **kwargs):
        return await mongo.delete_one("reading_history", *args, **kwargs)

    @classmethod
    async def update_list(cls, *args, **kwargs):
        return await mongo.update_one("reading_lists", *args, **kwargs)

    @classmethod
    async def insert_list(cls, *args, **kwargs):
        return await mongo.insert_one("reading_lists", *args, **kwargs)

    @classmethod
    async def find_list(cls, *args, **kwargs):
        return await mongo.find_one("reading_lists", *args, **kwargs)

    @classmethod
    async def insert_one(cls, *args, **kwargs):
        return await mongo.insert_one("reading_history", *args, **kwargs)

    @classmethod
    async def insert_many(cls, *args, **kwargs):
        return await mongo.insert_many("reading_history", *args, **kwargs)

    @classmethod
    async def find_one(cls, *args, **kwargs):
        return await mongo.find_one("reading_history", *args, **kwargs)

    @classmethod
    async def update_one(cls, *args, **kwargs):
        return await mongo.update_one("reading_history", *args, **kwargs)

    @classmethod
    async def update_many(cls, *args, **kwargs):
        return await mongo.update_many("reading_history", *args, **kwargs)

    @classmethod
    async def delete_one(cls, *args, **kwargs):
        return await mongo.delete_one("reading_history", *args, **kwargs)

    @classmethod
    async def delete_many(cls, *args, **kwargs):
        return await mongo.delete_many("reading_history", *args, **kwargs)

    @classmethod
    async def count_documents(cls, *args, **kwargs):
        return await mongo.count_documents("reading_history", *args, **kwargs)

    @classmethod
    def find(cls, *args, **kwargs):
        return mongo.find("reading_history", *args, **kwargs)

    @classmethod
    def aggregate(cls, *args, **kwargs):
        return mongo.aggregate("reading_history", *args, **kwargs)

class DocumentRepository:
    @classmethod
    async def find_one(cls, *args, **kwargs):
        return await mongo.find_one("documents", *args, db_name=settings.CONTENT_DB_NAME, **kwargs)

    @classmethod
    def find(cls, *args, **kwargs):
        return mongo.find("documents", *args, db_name=settings.CONTENT_DB_NAME, **kwargs)
