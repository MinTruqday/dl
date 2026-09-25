import hashlib
import hmac
from datetime import datetime, timezone
from uuid import uuid4

from src.core.infrastructure.configuration import settings
from src.core.infrastructure.mongo import mongo


class RetrievalAuditService:
    @staticmethod
    async def record(operation: str, query: str, requester_id: str | None, is_admin: bool, docs):
        metadata = [doc.get("metadata") or {} for doc in docs]
        await mongo.get_db().retrieval_audit.insert_one(
            {
                "_id": f"KNOWLEDGE-AUD-{uuid4().hex}",
                "operation": operation,
                "requester_id": requester_id or "unknown",
                "is_admin": bool(is_admin),
                "project_ids": sorted(
                    {str(item["project_id"]) for item in metadata if item.get("project_id")}
                ),
                "document_ids": sorted(
                    {str(item["document_id"]) for item in metadata if item.get("document_id")}
                ),
                "chunk_count": len(docs),
                "query_sha256": hmac.new(
                    settings.SECRET_KEY.encode("utf-8"), query.encode("utf-8"), hashlib.sha256
                ).hexdigest(),
                "created_at": datetime.now(timezone.utc),
            }
        )

    @staticmethod
    async def list(
        requester_id: str | None,
        project_id: str | None,
        document_id: str | None,
        limit: int,
    ):
        query = {}
        if requester_id:
            query["requester_id"] = requester_id
        if project_id:
            query["project_ids"] = project_id
        if document_id:
            query["document_ids"] = document_id
        return (
            await mongo.get_db()
            .retrieval_audit.find(query)
            .sort("created_at", -1)
            .limit(limit)
            .to_list(limit)
        )
