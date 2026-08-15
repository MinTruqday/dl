from datetime import datetime, timezone
import uuid

from loguru import logger

from src.clients.content import exchange_collected_document


class Database:
    async def insert_document(self, document_data: dict):
        now = datetime.now(timezone.utc)
        document = {
            "_id": str(uuid.uuid4()),
            "created_at": now,
            "updated_at": now,
            **document_data,
        }
        identity = document.get("source_url") or document.get("file_url")
        if not identity:
            raise ValueError("Collected document requires a source identity")
        result = await exchange_collected_document("upsert_collected", document=document)
        logger.info("Collected document record persisted")
        return str(result["document_id"])

    async def update_document(self, document_id: str, update_data: dict):
        result = await exchange_collected_document(
            "update_collected",
            document_id=document_id,
            values=update_data,
        )
        return bool(result["updated"])


database = Database()
