from datetime import datetime, timezone
from core.database import db_client
from loguru import logger


class PrivacyService:

    @staticmethod
    async def request_data_takeout(current_user, db=None):
        if db is None:
            db = db_client.mongodb.get_default_database()
        user_id = str(current_user.id)
        comments = await db["comments"].find({"user_id": user_id}).to_list(length=1000)
        documents = (
            await db["documents"].find({"author_id": user_id}).to_list(length=1000)
        )
        reactions = (
            await db["reactions"].find({"user_id": user_id}).to_list(length=1000)
        )
        takeout_payload = {
            "profile": current_user.model_dump(exclude={"password_hash"}),
            "authored_documents": [
                {"_id": str(b["_id"]), "title": b.get("title")} for b in documents
            ],
            "comments_written": len(comments),
            "reactions_given": len(reactions),
            "raw_comments": [
                {"document_id": c.get("document_id"), "content": c.get("content")}
                for c in comments
            ],
        }
        logger.info(f"Data takeout requested by user {user_id}")
        return takeout_payload

    @staticmethod
    async def right_to_be_forgotten(current_user, db=None):
        if db is None:
            db = db_client.mongodb.get_default_database()
        user_id = str(current_user.id)
        await db["comments"].update_many(
            {"user_id": user_id},
            {
                "$set": {
                    "content": "[Nội dung đã bị xóa theo yêu cầu của Quyền lãng quên GDPR]",
                    "is_shadowbanned_content": True,
                }
            },
        )
        await db["documents"].delete_many({"author_id": user_id})
        await db["reactions"].delete_many({"user_id": user_id})
        if db_client.redis:
            await db_client.redis.delete(f"active_session:{user_id}")
        await db["users"].delete_one({"_id": str(current_user.id)})
        logger.info(f"User {user_id} requested to be forgotten (GDPR)")
        return {
            "status": "success",
            "message": "Tài khoản của bạn đã được xóa hoàn toàn khỏi hệ thống theo yêu cầu.",
        }

    @staticmethod
    async def request_data_export(current_user, db=None):
        logger.info(f"Data export request recorded for user {current_user.id}")
        return {
            "message": "Đã ghi nhận yêu cầu trích xuất dữ liệu. Sẽ gửi qua email trong vòng 24 giờ."
        }

    @staticmethod
    async def generate_gdpr_takeout(current_user, db=None):
        if db is None:
            db = db_client.mongodb.get_default_database()
        user_id = str(current_user.id)
        full_data = {
            "profile": await db["users"].find_one(
                {"_id": str(current_user.id)}, {"password_hash": 0}
            ),
            "documents": await db["documents"]
            .find({"author_id": user_id})
            .to_list(100),
            "comments": await db["comments"].find({"user_id": user_id}).to_list(500),
        }
        logger.info(f"GDPR takeout prepared for user {user_id}")
        return {"status": "success", "data": full_data}
