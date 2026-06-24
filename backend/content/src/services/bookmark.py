from src.core.infrastructure.api_client import db_client
import uuid
from datetime import datetime, timezone

from fastapi import HTTPException, Query
from loguru import logger
from uuid6 import uuid7

from src.core.infrastructure.configuration import settings
from src.core.infrastructure.database import database
from src.repositories.profile import ContentProfileRepository
from src.repositories.document import DocumentRepository
from src.repositories.bookmark import BookmarkRepository


class BookmarkService:

    @staticmethod
    async def toggle_bookmark(document_id: str, current_user, db=None) -> dict:
        if db is None:
            db = database.mongodb.get_default_database()
        user_id = str(current_user.id)
        profile = await ContentProfileRepository.find_content_profile(
            {"_id": user_id}, projection={"bookmarks": 1}
        )
        bookmarks = profile.get("bookmarks", []) if profile else []
        if document_id in bookmarks:
            bookmarks.remove(document_id)
            message = "The specified document has been successfully removed from your personal archive collection"
            is_bookmarked = False
            await ContentProfileRepository.update_content_profile(
                {"_id": user_id},
                {
                    "$pull": {"bookmarks": document_id},
                    "$set": {"updated_at": datetime.now(timezone.utc)},
                },
                upsert=True,
            )
        else:
            bookmarks.append(document_id)
            message = "The specified document has been successfully added to your personal archive collection"
            is_bookmarked = True
            await ContentProfileRepository.update_content_profile(
                {"_id": user_id},
                {
                    "$addToSet": {"bookmarks": document_id},
                    "$set": {"updated_at": datetime.now(timezone.utc)},
                },
                upsert=True,
            )
        return {"status": "success", "message": message, "is_bookmarked": is_bookmarked}

    @staticmethod
    async def get_bookmarks(
        current_user,
        limit: int = Query(
            default=settings.DEFAULT_PAGE_LIMIT, le=settings.MAX_PAGE_LIMIT
        ),
        db=None,
    ) -> list:
        if db is None:
            db = database.mongodb.get_default_database()
        profile = await ContentProfileRepository.find_content_profile(
            {"_id": str(current_user.id)}, projection={"bookmarks": 1}
        )
        bookmark_ids = profile.get("bookmarks", []) if profile else []
        if not bookmark_ids:
            return []
        docs = (
            await DocumentRepository
            .find({"_id": {"$in": bookmark_ids}})
            .limit(limit)
            .execute()
        )
        return [
            {
                "_id": str(d["_id"]),
                "title": d.get("title", ""),
                "slug": d.get("slug", ""),
                "cover_url": d.get("cover_url"),
                "author_name": d.get("author_name", "DocLib Author"),
                "views": d.get("views", 0),
                "created_at": (
                    d["created_at"].isoformat()
                    if isinstance(d.get("created_at"), datetime)
                    else None
                ),
            }
            for d in docs
        ]

    @staticmethod
    async def create_bookmark_folder(name: str, current_user, db=None) -> dict:
        if db is None:
            db = database.mongodb.get_default_database()
        folder = {
            "_id": str(uuid7()),
            "user_id": str(current_user.id),
            "name": name.strip()[:100],
            "bookmark_ids": [],
            "created_at": datetime.now(timezone.utc),
        }
        await BookmarkRepository.insert_folder(folder)
        logger.info("Tạo thư mục dấu trang thành công")
        return folder

    @staticmethod
    async def get_bookmark_folders(current_user, db=None) -> list:
        if db is None:
            db = database.mongodb.get_default_database()
        folders = (
            await BookmarkFolderRepository
            .find({"user_id": str(current_user.id)})
            .sort("created_at", -1)
            .execute()
        )
        return [
            {
                "_id": str(f["_id"]),
                "name": f.get("name", ""),
                "bookmark_ids": f.get("bookmark_ids", []),
                "created_at": (
                    f["created_at"].isoformat()
                    if isinstance(f.get("created_at"), datetime)
                    else None
                ),
            }
            for f in folders
        ]

    @staticmethod
    async def assign_bookmarks_to_folder(
        folder_id: str, bookmark_ids: list, current_user, db=None
    ) -> dict:
        if db is None:
            db = database.mongodb.get_default_database()
        result = await BookmarkRepository.update_folder(
            {"_id": folder_id, "user_id": str(current_user.id)},
            {
                "$set": {
                    "bookmark_ids": bookmark_ids,
                    "updated_at": datetime.now(timezone.utc),
                }
            },
        )
        if result.matched_count == 0:
            raise HTTPException(
                status_code=404, detail="Không tìm thấy thư mục dấu trang"
            )
        return {"message": "Cập nhật thư mục dấu trang thành công"}

    @staticmethod
    async def delete_bookmark_folder(folder_id: str, current_user, db=None) -> dict:
        if db is None:
            db = database.mongodb.get_default_database()
        result = await BookmarkRepository.delete_folder(
            {"_id": folder_id, "user_id": str(current_user.id)}
        )
        if result.deleted_count == 0:
            raise HTTPException(
                status_code=404, detail="Không tìm thấy thư mục dấu trang"
            )
        return {"message": "Xóa vĩnh viễn thư mục dấu trang thành công"}
