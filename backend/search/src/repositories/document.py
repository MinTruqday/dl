from src.core.infrastructure.mongo import mongo

class DocumentRepository:
    @classmethod
    def find(cls, *args, **kwargs):
        return mongo.find("documents", *args, db_name=mongo.get_content_db().name, **kwargs)

    @classmethod
    async def find_one(cls, *args, **kwargs):
        return await mongo.find_one("documents", *args, db_name=mongo.get_content_db().name, **kwargs)

    @classmethod
    def aggregate(cls, *args, **kwargs):
        return mongo.aggregate("documents", *args, db_name=mongo.get_content_db().name, **kwargs)
