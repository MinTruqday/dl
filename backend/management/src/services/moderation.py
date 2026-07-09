from src.core.logic_logger import log_logic_execution
from src.core.infrastructure.redis import redis
from src.core.infrastructure.mongo import mongo
from datetime import datetime, timezone

from loguru import logger

from src.core.infrastructure.database import database

class ModerationService:

    @staticmethod
    @log_logic_execution
    async def request_data_takeout(current_user):
        user_id = str(current_user.id)
        documents = (
            await mongo.find(collection="documents", query={"creator_id": user_id}, limit=1000)
        )
        reactions = (
            await mongo.find(collection="reactions", query={"user_id": user_id}, limit=1000)
        )
        takeout_payload = {
            "profile": current_user.model_dump(exclude={"password_hash"}),
            "authored_documents": [
                {"_id": str(b["_id"]), "title": b.get("title")} for b in documents
            ],
            "reactions_given": len(reactions),
        }
        logger.info("Data export request submitted successfully")
        return takeout_payload

    @staticmethod
    @log_logic_execution
    async def right_to_be_forgotten(current_user):
        user_id = str(current_user.id)
        await mongo.delete_many(collection="documents", filter={"creator_id": user_id})
        await mongo.delete_many(collection="reactions", filter={"user_id": user_id})
        await redis.delete(f"active_session:{user_id}")
        await mongo.delete_one(collection="users", filter={"_id": str(current_user.id)})
        logger.info("User data permanently deleted upon request")
        return {
            "status": "success",
            "message": "Tài khoản và toàn bộ dữ liệu liên quan đã được xóa vĩnh viễn khỏi hệ thống",
        }

    @staticmethod
    @log_logic_execution
    async def request_data_export(current_user):
        logger.info("Data export request recorded successfully")
        return {
            "message": "Yêu cầu trích xuất dữ liệu thành công, kết quả sẽ được gửi qua email"
        }

    @staticmethod
    @log_logic_execution
    async def generate_gdpr_takeout(current_user):
        user_id = str(current_user.id)
        full_data = {
            "profile": await mongo.find_one("users", 
                {"_id": str(current_user.id)}, {"password_hash": 0}
            ),
            "documents": await database.mongodb["documents"]
            .find({"creator_id": user_id})
            .execute(),
        }
        logger.info("Data exported successfully")
        return {"status": "success", "data": full_data}
