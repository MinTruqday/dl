from src.core.api_client import db_client
from datetime import datetime, timezone

from loguru import logger

from src.core.infrastructure.database import database


class ModerationService:

    @staticmethod
    async def request_data_takeout(current_user, db=None):
        if db is None:
            db = database.mongodb.get_default_database()
        user_id = str(current_user.id)
        documents = (
            await db_client.find(collection="documents", query={"creator_id": user_id}, limit=1000)
        )
        reactions = (
            await db_client.find(collection="reactions", query={"user_id": user_id}, limit=1000)
        )
        takeout_payload = {
            "profile": current_user.model_dump(exclude={"password_hash"}),
            "authored_documents": [
                {"_id": str(b["_id"]), "title": b.get("title")} for b in documents
            ],
            "reactions_given": len(reactions),
        }
        logger.info("Đã gửi yêu cầu xuất dữ liệu")
        return takeout_payload

    @staticmethod
    async def right_to_be_forgotten(current_user, db=None):
        if db is None:
            db = database.mongodb.get_default_database()
        user_id = str(current_user.id)
        await db_client.delete_many(collection="documents", filter={"creator_id": user_id})
        await db_client.delete_many(collection="reactions", filter={"user_id": user_id})
        if database.redis:
            await database.redis.delete(f"active_session:{user_id}")
        await db_client.delete_one(collection="users", filter={"_id": str(current_user.id)})
        logger.info("Đã xóa dữ liệu vĩnh viễn theo yêu cầu")
        return {
            "status": "success",
            "message": "Tài khoản của bạn đã bị xóa vĩnh viễn",
        }

    @staticmethod
    async def request_data_export(current_user, db=None):
        logger.info("Yêu cầu xuất dữ liệu đã được ghi nhận")
        return {
            "message": "Yêu cầu xuất dữ liệu thành công, liên kết sẽ được gửi qua email"
        }

    @staticmethod
    async def generate_gdpr_takeout(current_user, db=None):
        if db is None:
            db = database.mongodb.get_default_database()
        user_id = str(current_user.id)
        full_data = {
            "profile": await db["users"].find_one(
                {"_id": str(current_user.id)}, {"password_hash": 0}
            ),
            "documents": await db["documents"]
            .find({"creator_id": user_id})
            .to_list(100),
        }
        logger.info("Xuất dữ liệu thành công")
        return {"status": "success", "data": full_data}
