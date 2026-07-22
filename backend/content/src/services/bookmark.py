from src.core.logic_logger import log_logic_execution
from src.core.infrastructure.mongo import mongo
import uuid
from datetime import datetime, timezone

from fastapi import HTTPException, Query
from loguru import logger
from uuid6 import uuid7

from src.core.infrastructure.configuration import settings
from src.core.infrastructure.database import database
from src.repositories.profile import ProfileRepository
from src.repositories.document import DocumentRepository
from src.repositories.bookmark import BookmarkRepository

class BookmarkService:

    @staticmethod
    @log_logic_execution
    async def toggle_bookmark(document_id: str, current_user) -> dict:
        user_id = str(current_user.id)
        profile = await ProfileRepository.get_profile(user_id)
        bookmarks = profile.get("bookmarks", []) if profile else []
        if document_id in bookmarks:
            bookmarks.remove(document_id)
            message = "Xóa tài liệu khỏi danh sách lưu trữ cá nhân hoàn tất"
            is_bookmarked = False
            await ProfileRepository.update_profile(
                user_id, {
                    "$pull": {"bookmarks": document_id},
                    "$set": {"updated_at": datetime.now(timezone.utc).isoformat()},
                }
            )
        else:
            bookmarks.append(document_id)
            message = "Thêm tài liệu vào danh sách lưu trữ cá nhân hoàn tất"
            is_bookmarked = True
            await ProfileRepository.update_profile(
                user_id, {
                    "$addToSet": {"bookmarks": document_id},
                    "$set": {"updated_at": datetime.now(timezone.utc).isoformat()},
                }
            )
        return {"status": "success", "message": message, "is_bookmarked": is_bookmarked}

    @staticmethod
    @log_logic_execution
    async def get_bookmarks(
        current_user,
        limit: int = Query(
            default=20, le=100
        ),
    ) -> list:
        profile = await ProfileRepository.get_profile(str(current_user.id))
        bookmark_ids = profile.get("bookmarks", []) if profile else []
        if not bookmark_ids:
            return []
        docs = (
            await DocumentRepository
            .find({"_id": {"$in": bookmark_ids}})
            .limit(limit)
            .to_list(length=limit)
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
    @log_logic_execution
    async def create_bookmark_folder(name: str, current_user) -> dict:
        folder = {
            "_id": str(uuid7()),
            "user_id": str(current_user.id),
            "name": name.strip()[:100],
            "bookmark_ids": [],
            "created_at": datetime.now(timezone.utc),
        }
        await BookmarkRepository.insert_folder(folder)
        logger.info("Bookmark folder created successfully")
        return folder

    @staticmethod
    @log_logic_execution
    async def get_bookmark_folders(current_user) -> list:
        folders = (
            await mongo
            .find("bookmark_folders", {"user_id": str(current_user.id)})
            .sort("created_at", -1)
            .to_list(length=None)
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
    @log_logic_execution
    async def assign_bookmarks_to_folder(
        folder_id: str, bookmark_ids: list, current_user
    ) -> dict:
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
                status_code=404, detail="Hệ thống không tìm thấy thư mục dấu trang yêu cầu"
            )
        return {"message": "Cập nhật thông tin thư mục dấu trang hoàn tất"}

    @staticmethod
    @log_logic_execution
    async def delete_bookmark_folder(folder_id: str, current_user) -> dict:
        result = await BookmarkRepository.delete_folder(
            {"_id": folder_id, "user_id": str(current_user.id)}
        )
        if result.deleted_count == 0:
            raise HTTPException(
                status_code=404, detail="Hệ thống không tìm thấy thư mục dấu trang yêu cầu"
            )
        return {"message": "Thư mục dấu trang đã được xóa vĩnh viễn khỏi hệ thống"}
