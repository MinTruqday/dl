from src.core.infrastructure.api_client import db_client
from typing import Optional, Dict, Any, List
from src.core.infrastructure.database import database
from src.core.infrastructure.configuration import settings

class GroupRepository:
    @staticmethod
    def _get_db():
        db_name = settings.SERVICE_DB_NAME if hasattr(settings, 'SERVICE_DB_NAME') else 'doclib'
        return database.mongodb.get_database(db_name)

    @classmethod
    async def find_one(cls, *args, **kwargs):
        return await db_client.find_one("chat_groups", *args, **kwargs)

    @classmethod
    def find(cls, query: Dict[str, Any]):
        return db_client.query("chat_groups").filter(query)
