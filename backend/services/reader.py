from core.database import db_client
from fastapi import HTTPException
from datetime import datetime
import uuid
from loguru import logger

class ReaderService:
    @staticmethod
    async def get_privacy_settings(current_user) -> dict:
        db = db_client.mongodb.get_default_database()
        user = await db["users"].find_one({"_id": str(current_user.id)})
        return {
            "hide_reading_activity": user.get("privacy_hide_reading", False) if user else False, 
            "hide_library": user.get("privacy_hide_library", False) if user else False
        }

    @staticmethod
    async def update_privacy_settings(data: dict, current_user) -> dict:
        db = db_client.mongodb.get_default_database()
        await db["users"].update_one(
            {"_id": str(current_user.id)}, 
            {"$set": {
                "privacy_hide_reading": data.get("hide_reading_activity", False), 
                "privacy_hide_library": data.get("hide_library", False), 
                "updated_at": datetime.utcnow()
            }}
        )
        logger.info(f"Identity: Privacy settings updated for {current_user.id}")
        return {"message": "Đã cập nhật cài đặt riêng tư."}

    @staticmethod
    async def update_general_settings(new_settings: dict, current_user) -> dict:
        db = db_client.mongodb.get_default_database()
        user = await db["users"].find_one({"_id": str(current_user.id)})
        current_settings = user.get("settings", {}) if user else {}
        current_settings.update(new_settings)
        
        await db["users"].update_one(
            {"_id": str(current_user.id)}, 
            {"$set": {"settings": current_settings, "updated_at": datetime.utcnow()}}
        )
        logger.info(f"Identity: General settings updated for {current_user.id}")
        return {"message": "Đã cập nhật tùy chỉnh hệ thống thành công."}

    @staticmethod
    async def share_excerpt(data: dict, current_user) -> dict:
        db = db_client.mongodb.get_default_database()
        doc = await db["documents"].find_one({"_id": data["document_id"]})
        if not doc: 
            raise HTTPException(status_code=404, detail="Tài liệu không tồn tại.")
            
        excerpt_post = {
            "_id": str(uuid.uuid4()), 
            "user_id": str(current_user.id), 
            "content": data.get("caption", ""), 
            "item_type": "excerpt", 
            "excerpt_text": data["text"], 
            "attached_document_id": data["document_id"], 
            "attached_document_title": doc.get("title", ""), 
            "privacy": "public", 
            "created_at": datetime.utcnow()
        }
        await db["status_updates"].insert_one(excerpt_post)
        logger.info(f"Social: Excerpt shared by {current_user.id} from {data['document_id']}")
        return {"message": "Đã chia sẻ trích đoạn.", "post_id": excerpt_post["_id"]}
