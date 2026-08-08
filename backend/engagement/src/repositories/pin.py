from src.core.infrastructure.mongo import mongo

class PinRepository:
    @classmethod
    async def update_one(cls, *args, **kwargs):
        return await mongo.update_one("user_pins", *args, **kwargs)

    @classmethod
    async def find_one(cls, *args, **kwargs):
        return await mongo.find_one("user_pins", *args, **kwargs)

    @classmethod
    async def insert_one(cls, *args, **kwargs):
        return await mongo.insert_one("user_pins", *args, **kwargs)

    @classmethod
    async def delete_one(cls, *args, **kwargs):
        return await mongo.delete_one("user_pins", *args, **kwargs)

    @classmethod
    def find(cls, *args, **kwargs):
        return mongo.find("user_pins", *args, **kwargs)
