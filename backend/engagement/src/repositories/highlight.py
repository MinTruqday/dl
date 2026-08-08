from src.core.infrastructure.mongo import mongo

class HighlightRepository:
    @classmethod
    async def update_one(cls, *args, **kwargs):
        return await mongo.update_one("highlights", *args, **kwargs)

    @classmethod
    async def delete_one(cls, *args, **kwargs):
        return await mongo.delete_one("highlights", *args, **kwargs)

    @classmethod
    async def insert_one(cls, *args, **kwargs):
        return await mongo.insert_one("highlights", *args, **kwargs)

    @classmethod
    async def insert_many(cls, *args, **kwargs):
        return await mongo.insert_many("highlights", *args, **kwargs)

    @classmethod
    async def find_one(cls, *args, **kwargs):
        return await mongo.find_one("highlights", *args, **kwargs)

    @classmethod
    async def update_many(cls, *args, **kwargs):
        return await mongo.update_many("highlights", *args, **kwargs)

    @classmethod
    async def delete_many(cls, *args, **kwargs):
        return await mongo.delete_many("highlights", *args, **kwargs)

    @classmethod
    async def count_documents(cls, *args, **kwargs):
        return await mongo.count_documents("highlights", *args, **kwargs)

    @classmethod
    def find(cls, *args, **kwargs):
        return mongo.find("highlights", *args, **kwargs)

    @classmethod
    def aggregate(cls, *args, **kwargs):
        return mongo.aggregate("highlights", *args, **kwargs)
