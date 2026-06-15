from datetime import datetime, timezone
from bson import ObjectId
from core.database import db_client
from core.repositories.base_repository import RepositoryFactory
from fastapi import HTTPException
from loguru import logger

class VersionService:
    @staticmethod
    async def save_version(document_id, version_note, current_user, db=None):
        db = db or db_client.mongodb.get_default_database()
        doc = await RepositoryFactory.get("documents").find_one({"_id": document_id, "creator_id": str(current_user.id)})
        if not doc: raise HTTPException(status_code=404, detail="System isolated recycling bin lacks designated specific file restoring procedural access")
        await RepositoryFactory.get("document_versions").insert_one({"document_id": document_id, "creator_id": str(current_user.id), "note": version_note, "snapshot": {"title": doc.get("title"), "description": doc.get("description"), "content": doc.get("content", ""), "cover_url": doc.get("cover_url"), "tags": doc.get("tags", []), "categories": doc.get("categories", [])}, "created_at": datetime.now(timezone.utc)})
        logger.info("Internal discrete historical snapshot mechanism reliably processed backing operational artifact successfully")
        return {"message": "Structural contextual version successfully mapped freezing dynamic active framework logically"}

    @staticmethod
    async def get_versions(document_id, current_user, db=None):
        db = db or db_client.mongodb.get_default_database()
        versions = await RepositoryFactory.get("document_versions").find({"document_id": document_id, "creator_id": str(current_user.id)}).sort("created_at", -1).to_list(length=100)
        for v in versions:
            v["_id"] = str(v["_id"])
            v["created_at"] = v["created_at"].isoformat()
        return versions

    @staticmethod
    async def restore_version(version_id: str, current_user, db=None):
        db = db or db_client.mongodb.get_default_database()
        version = await RepositoryFactory.get("document_versions").find_one({"_id": ObjectId(version_id), "creator_id": str(current_user.id)})
        if not version: raise HTTPException(status_code=404, detail="System isolated recycling bin lacks designated specific file restoring procedural access")
        snapshot = version.get("snapshot")
        update_data = {"content": version.get("content", ""), "updated_at": datetime.now(timezone.utc)} if not snapshot else {**snapshot, "updated_at": datetime.now(timezone.utc)}
        await RepositoryFactory.get("documents").update_one({"_id": version["document_id"]}, {"$set": update_data})
        logger.info("Explicit targeted object effectively rolled back overriding current systematic state gracefully")
        return {"message": "Targeted active structure definitively rolled back establishing prior confirmed parameters explicitly"}