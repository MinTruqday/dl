from src.core.infrastructure.mongo import mongo
from src.core.infrastructure.database import database
from src.core.infrastructure.configuration import settings


class ChatRepository:
    """
    <module_purpose>
    <purpose>Handles direct MongoDB interactions for AI conversation data.</purpose>
    <metis_behavior>Isolates database logic from business rules. Fails safely on disconnected databases.</metis_behavior>
    </module_purpose>
    """

    @staticmethod
    def _get_db():
        db_name = settings.AI_DB_NAME
        return database.mongodb.get_database(db_name)

    @classmethod
    async def insert_ai_message(cls, *args, **kwargs):
        return await mongo.insert_one("ai_messages", *args, **kwargs)

    @classmethod
    async def find_ai_message(cls, *args, **kwargs):
        return await mongo.find_one("ai_messages", *args, **kwargs)

    @classmethod
    async def update_ai_session(cls, *args, **kwargs):
        return await mongo.update_one("ai_sessions", *args, **kwargs)

    @classmethod
    async def delete_ai_session(cls, *args, **kwargs):
        return await mongo.delete_one("ai_sessions", *args, **kwargs)

    @classmethod
    async def insert_ai_session(cls, *args, **kwargs):
        return await mongo.insert_one("ai_sessions", *args, **kwargs)

    @classmethod
    async def find_ai_session(cls, *args, **kwargs):
        return await mongo.find_one("ai_sessions", *args, **kwargs)

    @classmethod
    def find_ai_sessions(cls, *args, **kwargs):
        return mongo.find("ai_sessions", *args, **kwargs)

    @classmethod
    def find_ai_messages(cls, *args, **kwargs):
        return mongo.find("ai_messages", *args, **kwargs)

    @classmethod
    async def insert_one(cls, *args, **kwargs):
        return await mongo.insert_one("ai_messages", *args, **kwargs)

    @classmethod
    async def insert_many(cls, *args, **kwargs):
        return await mongo.insert_many("ai_messages", *args, **kwargs)

    @classmethod
    async def find_one(cls, *args, **kwargs):
        return await mongo.find_one("ai_messages", *args, **kwargs)

    @classmethod
    async def update_one(cls, *args, **kwargs):
        return await mongo.update_one("ai_messages", *args, **kwargs)

    @classmethod
    async def update_many(cls, *args, **kwargs):
        return await mongo.update_many("ai_messages", *args, **kwargs)

    @classmethod
    async def delete_one(cls, *args, **kwargs):
        return await mongo.delete_one("ai_messages", *args, **kwargs)

    @classmethod
    async def delete_many(cls, *args, **kwargs):
        return await mongo.delete_many("ai_messages", *args, **kwargs)

    @classmethod
    async def count_documents(cls, *args, **kwargs):
        return await mongo.count_documents("ai_messages", *args, **kwargs)

    @classmethod
    def find(cls, *args, **kwargs):
        return mongo.find("ai_messages", *args, **kwargs)

    @classmethod
    def aggregate(cls, *args, **kwargs):
        return mongo.aggregate("ai_messages", *args, **kwargs)

    @classmethod
    def query(cls, *args, **kwargs):
        return mongo.query("ai_messages", *args, **kwargs)
