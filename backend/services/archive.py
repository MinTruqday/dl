from core.database import db_client
from fastapi import HTTPException
from datetime import datetime, timezone
import uuid
from loguru import logger
from models.user import UserInDB
from typing import Any

class ArchiveService:
    @staticmethod
    async def get_archives(current_user, archive_type: str = "all", cursor: str = None, limit: int = 50) -> list:
        db = db_client.mongodb.get_default_database()
        
        if archive_type == "trash":
            query = {
                "author_id": str(current_user.id),
                "is_deleted": True
            }
        else:
            query = {
                "$or": [
                    {"author_id": str(current_user.id)},
                    {"shared_with": str(current_user.id)}
                ],
                "is_deleted": {"$ne": True}
            }
            if archive_type != "all":
                query["type"] = archive_type
            
        if cursor:
            query["_id"] = {"$lt": cursor}
        
        archives = await db["archives"].find(query).sort([("is_pinned", -1), ("_id", -1)]).limit(limit).to_list(length=limit)
        return [
            {
                "_id": str(a["_id"]),
                "author_id": a.get("author_id", ""),
                "owner_email": a.get("owner_email", ""),
                "filename": a.get("filename", ""),
                "type": a.get("type", "unknown"),
                "size_bytes": a.get("size_bytes", 0),
                "url": a.get("url", ""),
                "is_pinned": a.get("is_pinned", False),
                "is_deleted": a.get("is_deleted", False),
                "description": a.get("description", ""),
                "is_public": a.get("is_public", True),
                "shared_with": a.get("shared_with", []),
                "tags": a.get("tags", []),
                "created_at": a["created_at"].isoformat() if isinstance(a.get("created_at"), datetime) else a.get("created_at"),
            }
            for a in archives
        ]

    @staticmethod
    async def upload_archive(data: dict, current_user) -> dict:
        db = db_client.mongodb.get_default_database()
        archive_item = {
            "_id": str(uuid.uuid4()),
            "author_id": str(current_user.id),
            "owner_email": getattr(current_user, "email", ""),
            "filename": data["filename"],
            "type": data.get("type", "image"),
            "size_bytes": data.get("size_bytes", 0),
            "url": data["url"],
            "is_pinned": data.get("is_pinned", False),
            "is_deleted": data.get("is_deleted", False),
            "description": data.get("description", ""),
            "is_public": data.get("is_public", True),
            "shared_with": [],
            "tags": [],
            "created_at": datetime.now(timezone.utc),
        }
        await db["archives"].insert_one(archive_item)
        logger.info(f"Workspace: Author {current_user.id} uploaded archive {data['filename']}")
        return {"message": "Tải lên tệp tin thành công.", "archive": archive_item}

    @staticmethod
    async def delete_archive(archive_id: str, current_user) -> dict:
        db = db_client.mongodb.get_default_database()
        res = await db["archives"].update_one(
            {"_id": archive_id, "author_id": str(current_user.id)},
            {"$set": {"is_deleted": True}}
        )
        if res.matched_count == 0:
            raise HTTPException(status_code=404, detail="Tài nguyên không tồn tại.")
        logger.info(f"Workspace: Archive {archive_id} moved to trash by author {current_user.id}")
        return {"message": "Đã di chuyển tệp tin vào thùng rác."}

    @staticmethod
    async def rename_archive(archive_id: str, new_filename: str, current_user) -> dict:
        db = db_client.mongodb.get_default_database()
        res = await db["archives"].update_one(
            {"_id": archive_id, "author_id": str(current_user.id)},
            {"$set": {"filename": new_filename}}
        )
        if res.matched_count == 0:
            raise HTTPException(status_code=404, detail="Tài nguyên không tồn tại.")
        logger.info(f"Workspace: Archive {archive_id} renamed to {new_filename} by author {current_user.id}")
        return {"message": "Đổi tên tệp tin thành công."}

    @staticmethod
    async def toggle_pin_archive(archive_id: str, current_user) -> dict:
        db = db_client.mongodb.get_default_database()
        archive = await db["archives"].find_one({"_id": archive_id, "author_id": str(current_user.id)})
        if not archive:
            raise HTTPException(status_code=404, detail="Tài nguyên không tồn tại.")
        new_status = not archive.get("is_pinned", False)
        await db["archives"].update_one(
            {"_id": archive_id},
            {"$set": {"is_pinned": new_status}}
        )
        logger.info(f"Workspace: Archive {archive_id} pin status updated to {new_status} by author {current_user.id}")
        return {"message": "Cập nhật ghim tệp tin thành công.", "is_pinned": new_status}

    @staticmethod
    async def restore_archive(archive_id: str, current_user) -> dict:
        db = db_client.mongodb.get_default_database()
        res = await db["archives"].update_one(
            {"_id": archive_id, "author_id": str(current_user.id)},
            {"$set": {"is_deleted": False}}
        )
        if res.matched_count == 0:
            raise HTTPException(status_code=404, detail="Tài nguyên không tồn tại.")
        logger.info(f"Workspace: Archive {archive_id} restored by author {current_user.id}")
        return {"message": "Khôi phục tệp tin thành công."}

    @staticmethod
    async def permanently_delete_archive(archive_id: str, current_user) -> dict:
        db = db_client.mongodb.get_default_database()
        res = await db["archives"].delete_one({"_id": archive_id, "author_id": str(current_user.id)})
        if res.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Tài nguyên không tồn tại.")
        logger.info(f"Workspace: Archive {archive_id} permanently deleted by author {current_user.id}")
        return {"message": "Đã xóa vĩnh viễn tệp tin thành công."}

    @staticmethod
    async def update_description(archive_id: str, description: str, current_user) -> dict:
        db = db_client.mongodb.get_default_database()
        res = await db["archives"].update_one(
            {"_id": archive_id, "author_id": str(current_user.id)},
            {"$set": {"description": description}}
        )
        if res.matched_count == 0:
            raise HTTPException(status_code=404, detail="Tài nguyên không tồn tại.")
        logger.info(f"Workspace: Archive {archive_id} description updated by author {current_user.id}")
        return {"message": "Cập nhật mô tả tệp tin thành công."}

    @staticmethod
    async def toggle_visibility(archive_id: str, current_user) -> dict:
        db = db_client.mongodb.get_default_database()
        archive = await db["archives"].find_one({"_id": archive_id, "author_id": str(current_user.id)})
        if not archive:
            raise HTTPException(status_code=404, detail="Tài nguyên không tồn tại.")
        new_status = not archive.get("is_public", True)
        await db["archives"].update_one(
            {"_id": archive_id},
            {"$set": {"is_public": new_status}}
        )
        logger.info(f"Workspace: Archive {archive_id} visibility toggled to {new_status} by author {current_user.id}")
        return {"message": "Cập nhật trạng thái hiển thị thành công.", "is_public": new_status}

    @staticmethod
    async def share_archive(archive_id: str, email: str, current_user) -> dict:
        db = db_client.mongodb.get_default_database()
        target_user = await db["users"].find_one({"email": email})
        if not target_user:
            raise HTTPException(status_code=404, detail="Không tìm thấy tài khoản người dùng với email đã nhập.")
        
        target_user_id = str(target_user["_id"])
        if target_user_id == str(current_user.id):
            raise HTTPException(status_code=400, detail="Bạn không thể chia sẻ tệp tin cho chính mình.")
            
        archive = await db["archives"].find_one({"_id": archive_id, "author_id": str(current_user.id)})
        if not archive:
            raise HTTPException(status_code=404, detail="Tài nguyên không tồn tại hoặc bạn không có quyền chia sẻ.")
            
        shared_list = archive.get("shared_with", [])
        if target_user_id in shared_list:
            return {"message": "Tệp tin đã được chia sẻ cho người dùng này trước đó."}
            
        await db["archives"].update_one(
            {"_id": archive_id},
            {"$push": {"shared_with": target_user_id}}
        )
        logger.info(f"Workspace: Archive {archive_id} shared with user {target_user_id} by author {current_user.id}")
        return {"message": f"Chia sẻ tệp tin thành công tới {email}."}

    @staticmethod
    async def update_tags(archive_id: str, tags: list[str], current_user) -> dict:
        db = db_client.mongodb.get_default_database()
        res = await db["archives"].update_one(
            {"_id": archive_id, "author_id": str(current_user.id)},
            {"$set": {"tags": tags}}
        )
        if res.matched_count == 0:
            raise HTTPException(status_code=404, detail="Tài nguyên không tồn tại.")
        logger.info(f"Workspace: Archive {archive_id} tags updated to {tags} by author {current_user.id}")
        return {"message": "Cập nhật danh sách nhãn thành công."}

    @staticmethod
    async def upload_media(file, current_user: UserInDB):
        from core.storage import upload_file
        ext = file.filename.split(".")[-1].lower()
        if ext not in ["jpg", "jpeg", "png", "gif", "webp", "mp4"]:
            raise HTTPException(status_code=400, detail="Hệ thống chỉ hỗ trợ các định dạng tệp ảnh hoặc video mp4")
        
        filename = f"social/{uuid.uuid4().hex}.{ext}"
        content = await file.read()
        
        try:
            await upload_file(content, filename, file.content_type)
        except Exception as e:
            logger.error(f"MinIO media upload error: {e}")
            raise HTTPException(status_code=500, detail="Lỗi hệ thống khi tải tệp đa phương tiện lên MinIO")
            
        logger.info(f"Media uploaded by user {current_user.id}: {filename}")
        
        await ArchiveService.upload_archive({
            "filename": filename,
            "type": "image" if ext != "mp4" else "video",
            "size_bytes": len(content),
            "url": filename
        }, current_user)
        
        return {"url": filename, "type": "image" if ext != "mp4" else "video"}
