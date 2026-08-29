from src.core.infrastructure.database import database as ai_database
from src.knowledge.core.infrastructure.configuration import settings


class Database:
    @property
    def mongodb(self):
        if ai_database.mongodb is None:
            return None
        return ai_database.mongodb[settings.AI_DB_NAME]


database = Database()


async def init_db():
    if database.mongodb is None:
        raise RuntimeError("AI database must be initialized before knowledge subsystem")
    await database.mongodb.retrieval_audit.create_index([("requester_id", 1), ("created_at", -1)])
    await database.mongodb.retrieval_audit.create_index([("document_ids", 1), ("created_at", -1)])


async def close_db():
    return None


def get_db():
    return database.mongodb
