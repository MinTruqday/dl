from src.core.infrastructure.mongo import mongo
from typing import Optional, Dict, Any, List
from src.core.infrastructure.database import database
from src.core.infrastructure.configuration import settings

class ChatGroupRepository:
    @staticmethod
    def _get_db():
        db_name = settings.SERVICE_DB_NAME if hasattr(settings, 'SERVICE_DB_NAME') else 'doclib'
        return database.mongodb.get_database(db_name)

    @classmethod
    async def find_one(cls, query: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        return await mongo.find_one("chat_groups", query)

    @classmethod
    def find(cls, query: Dict[str, Any]):
        return mongo.query("chat_groups").filter(query)
