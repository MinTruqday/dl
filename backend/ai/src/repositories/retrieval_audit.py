from src.core.infrastructure.mongo import mongo


class RetrievalAuditRepository:
    async def insert(self, value):
        await mongo.insert_one("retrieval_audit", value)

    async def list(self, query, limit):
        return await mongo.find("retrieval_audit", query).sort("created_at", -1).limit(limit).to_list(limit)


retrieval_audit_repository = RetrievalAuditRepository()
