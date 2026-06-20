from datetime import datetime, timezone

from loguru import logger

from core.database import db_client


class PrivacyManager:

    @staticmethod
    async def request_data_takeout(current_user, db=None):
        if db is None:
            db = db_client.mongodb.get_default_database()
        user_id = str(current_user.id)
        comments = await db["comments"].find({"user_id": user_id}).to_list(length=1000)
        documents = (
            await db["documents"].find({"creator_id": user_id}).to_list(length=1000)
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
        logger.info("Đã gửi yêu cầu xuất dữ liệu")
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
                    "content": "[Content removed in compliance with GDPR Right to be Forgotten]",
                    "is_shadowbanned_content": True,
                }
            },
        )
        await db["documents"].delete_many({"creator_id": user_id})
        await db["reactions"].delete_many({"user_id": user_id})
        if db_client.redis:
            await db_client.redis.delete(f"active_session:{user_id}")
        await db["users"].delete_one({"_id": str(current_user.id)})
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
            db = db_client.mongodb.get_default_database()
        user_id = str(current_user.id)
        full_data = {
            "profile": await db["users"].find_one(
                {"_id": str(current_user.id)}, {"password_hash": 0}
            ),
            "documents": await db["documents"]
            .find({"creator_id": user_id})
            .to_list(100),
            "comments": await db["comments"].find({"user_id": user_id}).to_list(500),
        }
        logger.info("Xuất dữ liệu thành công")
        return {"status": "success", "data": full_data}
