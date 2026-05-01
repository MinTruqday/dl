from core.database import db_client
from datetime import datetime
import uuid
from loguru import logger

class SystemConfigService:
    @staticmethod
    async def manage_tags(action: str, tag_name: str, current_moderator) -> dict:
        db = db_client.mongodb.get_default_database()
        if action == "create":
            await db["system_tags"].insert_one({
                "_id": str(uuid.uuid4()), 
                "name": tag_name.lower(), 
                "created_at": datetime.utcnow()
            })
            logger.info(f"System: Tag '{tag_name}' created by {current_moderator.id}")
            return {"message": f"Đã tạo thẻ '{tag_name}' thành công."}
        elif action == "delete":
            await db["system_tags"].delete_one({"name": tag_name.lower()})
            logger.info(f"System: Tag '{tag_name}' deleted by {current_moderator.id}")
            return {"message": f"Đã xóa thẻ '{tag_name}' thành công."}
        return {"message": "Hành động không hợp lệ."}

    @staticmethod
    async def get_all_tags() -> list:
        db = db_client.mongodb.get_default_database()
        tags = await db["system_tags"].find().to_list(length=200)
        return [{"id": t["_id"], "name": t.get("name", "")} for t in tags]

    @staticmethod
    async def manage_blacklist(action: str, keyword: str, current_moderator) -> dict:
        db = db_client.mongodb.get_default_database()
        if action == "add":
            await db["blacklist_keywords"].insert_one({
                "_id": str(uuid.uuid4()), 
                "keyword": keyword.lower(), 
                "created_at": datetime.utcnow()
            })
            logger.info(f"System: Keyword '{keyword}' blacklisted by {current_moderator.id}")
            return {"message": f"Đã thêm '{keyword}' vào danh sách cấm."}
        elif action == "remove":
            await db["blacklist_keywords"].delete_one({"keyword": keyword.lower()})
            logger.info(f"System: Keyword '{keyword}' removed from blacklist by {current_moderator.id}")
            return {"message": f"Đã xóa '{keyword}' khỏi danh sách cấm."}
        return {"message": "Hành động không hợp lệ."}

    @staticmethod
    async def get_blacklist() -> list:
        db = db_client.mongodb.get_default_database()
        keywords = await db["blacklist_keywords"].find().to_list(length=500)
        return [{"id": k["_id"], "keyword": k.get("keyword", "")} for k in keywords]

    @staticmethod
    async def set_nsfw_sensitivity(level: str, current_moderator) -> dict:
        db = db_client.mongodb.get_default_database()
        await db["system_config"].update_one(
            {"key": "nsfw_filter_level"}, 
            {"$set": {"value": level, "updated_at": datetime.utcnow()}}, 
            upsert=True
        )
        logger.info(f"System: NSFW sensitivity set to '{level}' by {current_moderator.id}")
        return {"message": f"Thiết lập bộ lọc NSFW mức '{level}' thành công."}
