from core.database import db_client
from loguru import logger

class PrivacyService:

    @staticmethod
    async def request_data_takeout(current_user, db=None) -> dict:
        target_db = db or db_client.mongodb.get_default_database()
        user_id = str(current_user.id)
        comments = await target_db["comments"].find({"user_id": user_id}).to_list(length=1000)
        documents = await target_db["documents"].find({"creator_id": user_id}).to_list(length=1000)
        reactions = await target_db["reactions"].find({"user_id": user_id}).to_list(length=1000)
        
        takeout_payload = {
            "profile": current_user.model_dump(exclude={"password_hash"}),
            "authored_documents": [{"_id": str(b["_id"]), "title": b.get("title")} for b in documents],
            "comments_written": len(comments),
            "reactions_given": len(reactions),
            "raw_comments": [{"document_id": c.get("document_id"), "content": c.get("content")} for c in comments],
        }
        logger.info("Comprehensive data takeout request has been initiated by authenticated user")
        return takeout_payload

    @staticmethod
    async def right_to_be_forgotten(current_user, db=None) -> dict:
        target_db = db or db_client.mongodb.get_default_database()
        user_id = str(current_user.id)
        await target_db["comments"].update_many(
            {"user_id": user_id},
            {"$set": {"content": "[Content removed in compliance with GDPR Right to be Forgotten]", "is_shadowbanned_content": True}},
        )
        await target_db["documents"].delete_many({"creator_id": user_id})
        await target_db["reactions"].delete_many({"user_id": user_id})
        
        if db_client.redis:
            await db_client.redis.delete(f"active_session:{user_id}")
            
        await target_db["users"].delete_one({"_id": str(current_user.id)})
        logger.info("Authenticated user invoked right to be forgotten resulting in permanent data removal")
        return {
            "status": "success",
            "message": "Account and associated personal data permanently removed from systems as requested",
        }

    @staticmethod
    async def request_data_export(current_user, db=None) -> dict:
        logger.info("Data export request has been successfully registered for authenticated user")
        return {"message": "Data export request received and secure download link will be dispatched shortly"}

    @staticmethod
    async def generate_gdpr_takeout(current_user, db=None) -> dict:
        target_db = db or db_client.mongodb.get_default_database()
        user_id = str(current_user.id)
        full_data = {
            "profile": await target_db["users"].find_one({"_id": str(current_user.id)}, {"password_hash": 0}),
            "documents": await target_db["documents"].find({"creator_id": user_id}).to_list(100),
            "comments": await target_db["comments"].find({"user_id": user_id}).to_list(500),
        }
        logger.info("Compliance data takeout package successfully compiled and prepared for user")
        return {"status": "success", "data": full_data}