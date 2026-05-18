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
        query = {"author_id": str(current_user.id)}
        
        if archive_type != "all":
            query["type"] = archive_type
            
        if cursor:
            from bson import ObjectId
            query["_id"] = {"$lt": ObjectId(cursor)}
        
        archives = await db["archives"].find(query).sort("_id", -1).limit(limit).to_list(length=limit)
        return [
            {
                "id": str(a["_id"]),
                "filename": a.get("filename", ""),
                "type": a.get("type", "unknown"),
                "size_bytes": a.get("size_bytes", 0),
                "url": a.get("url", ""),
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
            "filename": data["filename"],
            "type": data.get("type", "image"),
            "size_bytes": data.get("size_bytes", 0),
            "url": data["url"],
            "created_at": datetime.now(timezone.utc),
        }
        await db["archives"].insert_one(archive_item)
        logger.info(f"Workspace: Author {current_user.id} uploaded archive {data['filename']}")
        return {"message": "Tải lên tệp tin thành công.", "archive": archive_item}

    @staticmethod
    async def delete_archive(archive_id: str, current_user) -> dict:
        db = db_client.mongodb.get_default_database()
        res = await db["archives"].delete_one({"_id": archive_id, "author_id": str(current_user.id)})
        if res.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Tài nguyên không tồn tại.")
            
        logger.info(f"Workspace: Archive {archive_id} deleted by author {current_user.id}")
        return {"message": "Đã xóa tệp tin thành công."}

    @staticmethod
    async def upload_media(file, current_user: UserInDB):
        from core.storage import upload_file
        ext = file.filename.split(".")[-1].lower()
        if ext not in ["jpg", "jpeg", "png", "gif", "webp", "mp4"]:
            raise HTTPException(status_code=400, detail="Hệ thống chỉ hỗ trợ các định dạng tệp ảnh hoặc video mp4")
        
        filename = f"feed_uploads/{uuid.uuid4().hex}.{ext}"
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
