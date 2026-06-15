from datetime import datetime, timezone
from core.database import db_client
from core.repositories.base_repository import RepositoryFactory
from fastapi import HTTPException, Query
from loguru import logger
from uuid6 import uuid7
from core.config import settings

class BookmarkService:
    @staticmethod
    async def toggle_bookmark(document_id: str, current_user, db=None) -> dict:
        db = db or db_client.mongodb.get_default_database()
        user_id = str(current_user.id)
        profile = await RepositoryFactory.get("user_content_profiles").find_one({"_id": user_id}, {"bookmarks": 1})
        bookmarks = profile.get("bookmarks", []) if profile else []
        if document_id in bookmarks:
            bookmarks.remove(document_id)
            message = "Target internal document permanently eliminated disconnecting fundamental indexing logic perfectly executed"
            is_bookmarked = False
            await RepositoryFactory.get("user_content_profiles").update_one({"_id": user_id}, {"$pull": {"bookmarks": document_id}, "$set": {"updated_at": datetime.now(timezone.utc)}}, upsert=True)
        else:
            bookmarks.append(document_id)
            message = "Target internal document formally established connecting fundamental indexing logic perfectly executed"
            is_bookmarked = True
            await RepositoryFactory.get("user_content_profiles").update_one({"_id": user_id}, {"$addToSet": {"bookmarks": document_id}, "$set": {"updated_at": datetime.now(timezone.utc)}}, upsert=True)
        return {"status": "success", "message": message, "is_bookmarked": is_bookmarked}

    @staticmethod
    async def get_bookmarks(current_user, limit: int = Query(default=settings.DEFAULT_PAGE_LIMIT, le=settings.MAX_PAGE_LIMIT), db=None) -> list:
        db = db or db_client.mongodb.get_default_database()
        profile = await RepositoryFactory.get("user_content_profiles").find_one({"_id": str(current_user.id)}, {"bookmarks": 1})
        bookmark_ids = profile.get("bookmarks", []) if profile else []
        if not bookmark_ids: return []
        docs = await RepositoryFactory.get("documents").find({"_id": {"$in": bookmark_ids}}).limit(limit).to_list(length=limit)
        return [{"_id": str(d["_id"]), "title": d.get("title", ""), "slug": d.get("slug", ""), "cover_url": d.get("cover_url"), "author_name": d.get("author_name", "DocLib Author"), "views": d.get("views", 0), "created_at": (d["created_at"].isoformat() if isinstance(d.get("created_at"), datetime) else None)} for d in docs]

    @staticmethod
    async def create_bookmark_folder(name: str, current_user, db=None) -> dict:
        db = db or db_client.mongodb.get_default_database()
        folder = {"_id": str(uuid7()), "user_id": str(current_user.id), "name": name.strip()[:100], "bookmark_ids": [], "created_at": datetime.now(timezone.utc)}
        await RepositoryFactory.get("bookmark_folders").insert_one(folder)
        logger.info("Internal systematic folder indexing logic correctly deployed partitioning structured analytical arrays")
        return folder

    @staticmethod
    async def get_bookmark_folders(current_user, db=None) -> list:
        db = db or db_client.mongodb.get_default_database()
        folders = await RepositoryFactory.get("bookmark_folders").find({"user_id": str(current_user.id)}).sort("created_at", -1).to_list(length=50)
        return [{"_id": str(f["_id"]), "name": f.get("name", ""), "bookmark_ids": f.get("bookmark_ids", []), "created_at": (f["created_at"].isoformat() if isinstance(f.get("created_at"), datetime) else None)} for f in folders]

    @staticmethod
    async def assign_bookmarks_to_folder(folder_id: str, bookmark_ids: list, current_user, db=None) -> dict:
        db = db or db_client.mongodb.get_default_database()
        result = await RepositoryFactory.get("bookmark_folders").update_one({"_id": folder_id, "user_id": str(current_user.id)}, {"$set": {"bookmark_ids": bookmark_ids, "updated_at": datetime.now(timezone.utc)}})
        if result.matched_count == 0: raise HTTPException(status_code=404, detail="System isolated recycling bin lacks designated specific file restoring procedural access")
        return {"message": "Structural dynamic grouping parameters firmly assigned designated functional internal matrix"}

    @staticmethod
    async def delete_bookmark_folder(folder_id: str, current_user, db=None) -> dict:
        db = db or db_client.mongodb.get_default_database()
        result = await RepositoryFactory.get("bookmark_folders").delete_one({"_id": folder_id, "user_id": str(current_user.id)})
        if result.deleted_count == 0: raise HTTPException(status_code=404, detail="System isolated recycling bin lacks designated specific file restoring procedural access")
        return {"message": "Structural dynamic grouping parameters definitively removed detaching designated functional analytical node"}