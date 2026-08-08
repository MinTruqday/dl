from src.core.infrastructure.mongo import mongo

class CloudRepository:
    @classmethod
    def find(cls, *args, **kwargs):
        return mongo.find("storage_items", *args, db_name=mongo.get_cloud_db().name, **kwargs)

    @classmethod
    async def find_one(cls, *args, **kwargs):
        return await mongo.find_one("storage_items", *args, db_name=mongo.get_cloud_db().name, **kwargs)

    @classmethod
    async def update_one(cls, *args, **kwargs):
        return await mongo.update_one("storage_items", *args, db_name=mongo.get_cloud_db().name, **kwargs)
