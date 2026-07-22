from src.core.infrastructure.mongo import mongo


class AnnouncementRepository:
    @staticmethod
    def find(query: dict):
        return mongo.find("notifications", query)

    @staticmethod
    async def find_one(query: dict, projection: dict = None):
        return await mongo.find_one("notifications", query, projection)

    @staticmethod
    async def count_documents(query: dict):
        return await mongo.count_documents("notifications", query)

    @staticmethod
    async def insert_one(document: dict):
        return await mongo.insert_one("notifications", document)

    @staticmethod
    async def update_one(query: dict, update: dict):
        return await mongo.update_one("notifications", query, update)

    @staticmethod
    async def update_many(query: dict, update: dict):
        return await mongo.update_many("notifications", query, update)

    @staticmethod
    async def delete_one(query: dict):
        return await mongo.delete_one("notifications", query)

    @staticmethod
    async def get_settings(user_id: str):
        document = await mongo.find_one("notification_settings", {"_id": user_id})
        return document.get("settings", {}) if document else {}

    @staticmethod
    async def update_settings(user_id: str, settings: dict):
        return await mongo.update_one(
            "notification_settings",
            {"_id": user_id},
            {"$set": {"settings": settings}},
            upsert=True,
        )
