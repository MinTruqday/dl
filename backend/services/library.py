from core.database import db_client
from fastapi import HTTPException
from datetime import datetime, timezone
import uuid
from loguru import logger

class LibraryService:
    @staticmethod
    async def create_reading_list(data, current_user):
        db = db_client.mongodb.get_default_database()
        new_list = {
            "_id": str(uuid.uuid4()), 
            "user_id": str(current_user.id), 
            "name": data.name, 
            "description": data.description, 
            "is_public": data.is_public, 
            "documents": [], 
            "created_at": datetime.now(timezone.utc)
        }
        await db["reading_lists"].insert_one(new_list)
        logger.info("Log message sanitized")
        return new_list

    @staticmethod
    async def get_my_reading_lists(current_user):
        db = db_client.mongodb.get_default_database()
        return await db["reading_lists"].find({"user_id": str(current_user.id)}).to_list(100)

    @staticmethod
    async def get_reading_list_by_id(list_id: str, current_user):
        db = db_client.mongodb.get_default_database()
        reading_list = await db["reading_lists"].find_one({"_id": list_id, "user_id": str(current_user.id)})
        if not reading_list:
            raise HTTPException(status_code=404, detail="Không tìm thấy danh sách đọc.")
        
        doc_ids = reading_list.get("documents", [])
        if doc_ids:
            docs = await db["documents"].find({"_id": {"$in": doc_ids}}).to_list(length=100)
            reading_list["documents_detailed"] = docs
        else:
            reading_list["documents_detailed"] = []
            
        return reading_list

    @staticmethod
    async def add_document_to_list(list_id: str, document_id: str, current_user) -> dict:
        db = db_client.mongodb.get_default_database()
        result = await db["reading_lists"].update_one(
            {"_id": list_id, "user_id": str(current_user.id)},
            {"$addToSet": {"documents": document_id}, "$set": {"updated_at": datetime.now(timezone.utc)}}
        )
        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="Không tìm thấy danh sách đọc.")
        return {"status": "success", "message": "Đã thêm vào danh sách."}

    @staticmethod
    async def remove_document_from_list(list_id: str, document_id: str, current_user) -> dict:
        db = db_client.mongodb.get_default_database()
        result = await db["reading_lists"].update_one(
            {"_id": list_id, "user_id": str(current_user.id)},
            {"$pull": {"documents": document_id}, "$set": {"updated_at": datetime.now(timezone.utc)}}
        )
        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="Không tìm thấy danh sách đọc.")
        return {"status": "success", "message": "Đã xóa khỏi danh sách."}

    @staticmethod
    async def create_bookmark_folder(name: str, current_user) -> dict:
        db = db_client.mongodb.get_default_database()
        folder = {
            "_id": str(uuid.uuid4()),
            "user_id": str(current_user.id),
            "name": name.strip()[:100],
            "bookmark_ids": [],
            "created_at": datetime.now(timezone.utc),
        }
        await db["bookmark_folders"].insert_one(folder)
        logger.info("Log message sanitized")
        return folder

    @staticmethod
    async def get_bookmark_folders(current_user) -> list:
        db = db_client.mongodb.get_default_database()
        folders = await db["bookmark_folders"].find(
            {"user_id": str(current_user.id)}
        ).sort("created_at", -1).to_list(length=50)
        return [{
            "id": str(f["_id"]),
            "name": f.get("name", ""),
            "bookmark_ids": f.get("bookmark_ids", []),
            "created_at": f["created_at"].isoformat() if isinstance(f.get("created_at"), datetime) else "",
        } for f in folders]

    @staticmethod
    async def assign_bookmarks_to_folder(folder_id: str, bookmark_ids: list, current_user) -> dict:
        db = db_client.mongodb.get_default_database()
        result = await db["bookmark_folders"].update_one(
            {"_id": folder_id, "user_id": str(current_user.id)},
            {"$set": {"bookmark_ids": bookmark_ids, "updated_at": datetime.now(timezone.utc)}}
        )
        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="Thư mục không tồn tại.")
        return {"message": "Đã cập nhật thư mục đánh dấu thành công."}

    @staticmethod
    async def delete_bookmark_folder(folder_id: str, current_user) -> dict:
        db = db_client.mongodb.get_default_database()
        result = await db["bookmark_folders"].delete_one({"_id": folder_id, "user_id": str(current_user.id)})
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Thư mục không tồn tại.")
        return {"message": "Đã xóa thư mục đánh dấu thành công."}

    @staticmethod
    async def get_bookmarks(current_user) -> list:
        db = db_client.mongodb.get_default_database()
        user = await db["users"].find_one({"_id": str(current_user.id)}, {"bookmarks": 1})
        bookmark_ids = user.get("bookmarks", []) if user else []
        if not bookmark_ids:
            return []
            
        docs = await db["documents"].find(
            {"_id": {"$in": bookmark_ids}}
        ).to_list(length=100)
        
        return [{
            "id": str(d["_id"]),
            "title": d.get("title", ""),
            "slug": d.get("slug", ""),
            "cover_url": d.get("cover_url"),
            "author_name": "Tác giả DocLib"
        } for d in docs]

    @staticmethod
    async def toggle_bookmark(document_id: str, current_user) -> dict:
        db = db_client.mongodb.get_default_database()
        user = await db["users"].find_one({"_id": str(current_user.id)}, {"bookmarks": 1})
        bookmarks = user.get("bookmarks", []) if user else []
        
        if document_id in bookmarks:
            bookmarks.remove(document_id)
            message = "Đã gỡ bỏ thực thể khỏi thư viện lưu trữ."
            is_bookmarked = False
        else:
            bookmarks.append(document_id)
            message = "Đã ghi nhận thực thể vào thư viện lưu trữ."
            is_bookmarked = True
            
        await db["users"].update_one(
            {"_id": str(current_user.id)},
            {"$set": {"bookmarks": bookmarks, "updated_at": datetime.now(timezone.utc)}}
        )
        return {"status": "success", "message": message, "is_bookmarked": is_bookmarked}
