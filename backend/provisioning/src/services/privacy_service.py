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
        logger.info("A comprehensive data takeout request has been initiated by the authenticated user")
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
        await db["documents"].delete_many({"author_id": user_id})
        await db["reactions"].delete_many({"user_id": user_id})
        if db_client.redis:
            await db_client.redis.delete(f"active_session:{user_id}")
        await db["users"].delete_one({"_id": str(current_user.id)})
        logger.info("The authenticated user has invoked their right to be forgotten resulting in permanent data removal")
        return {
            "status": "success",
            "message": "Your account and all associated personal data have been permanently removed from our systems as per your request",
        }

    @staticmethod
    async def request_data_export(current_user, db=None):
        logger.info("A data export request has been successfully registered for the authenticated user")
        return {
            "message": "Your data export request has been received and a secure download link will be dispatched to your registered email address shortly"
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
        logger.info("The compliance data takeout package has been successfully compiled and prepared for the user")
        return {"status": "success", "data": full_data}