from datetime import datetime, timezone
from core.database import db_client
from core.storage import upload_file
from fastapi import HTTPException
from loguru import logger
from uuid6 import uuid7

class IdentityService:

    @staticmethod
    async def become_author(current_user, db=None) -> dict:
        target_db = db or db_client.mongodb.get_default_database()
        user_id = str(current_user.get("id"))
        if current_user.get("role") != "reader":
            raise HTTPException(
                status_code=400,
                detail="Action restricted because only accounts with standard reader privileges can upgrade",
            )
        await target_db["users"].update_one(
            {"_id": user_id},
            {"$set": {"role": "author", "updated_at": datetime.now(timezone.utc)}},
        )
        logger.info("Access privileges for specified user account elevated to author role")
        return {"status": "success", "message": "Account successfully upgraded and granted full author publishing privileges"}

    @staticmethod
    async def apply_author(application, current_user, db=None) -> dict:
        target_db = db or db_client.mongodb.get_default_database()
        user_id = str(current_user.get("id"))
        if current_user.get("role") == "author":
            raise HTTPException(status_code=400, detail="Specified account already configured with full author privileges and capabilities")
        if current_user.get("role") != "reader":
            raise HTTPException(status_code=403, detail="Action restricted because only accounts with standard reader privileges can apply")
        if current_user.creator_status == CreatorStatusEnum.PENDING:
            raise HTTPException(status_code=400, detail="Previous application for author status is currently under active administrative review")
        if current_user.creator_status == CreatorStatusEnum.SUSPENDED:
            raise HTTPException(status_code=403, detail="Account is restricted by administration and cannot apply for elevated privileges")
            
        application_data = {
            "_id": str(uuid7()),
            "user_id": user_id,
            "portfolio_url": application.get("portfolio_url", "") if isinstance(application, dict) else "",
            "reason": application.get("reason", "") if isinstance(application, dict) else (application if isinstance(application, str) else ""),
            "status": CreatorStatusEnum.PENDING,
            "created_at": datetime.now(timezone.utc),
        }
        await target_db["author_applications"].insert_one(application_data)
        await target_db["users"].update_one(
            {"_id": user_id},
            {"$set": {"creator_status": CreatorStatusEnum.PENDING, "tos_accepted_at": datetime.now(timezone.utc)}},
        )
        logger.info("Application for author privileges successfully submitted and recorded in queue")
        return {"status": "success", "message": "Author application submitted successfully and is awaiting administrative review"}

    @staticmethod
    async def upload_kyc(file, current_user, db=None) -> dict:
        target_db = db or db_client.mongodb.get_default_database()
        user_id = str(current_user.get("id"))
        if current_user.kyc_status == KYCStatusEnum.PENDING:
            raise HTTPException(status_code=400, detail="Submitted identity verification documents are currently under active administrative review")
        if current_user.kyc_status == KYCStatusEnum.VERIFIED:
            raise HTTPException(status_code=400, detail="Account identity has already been successfully verified by system administration")
            
        file_bytes = await file.read()
        file_ext = file.filename.split(".")[-1]
        object_name = f"kyc/{user_id}_{uuid7()}.{file_ext}"
        await upload_file(file_bytes, object_name, content_type=file.content_type)
        
        kyc_data = {
            "_id": str(uuid7()),
            "user_id": user_id,
            "document_url": object_name,
            "status": KYCStatusEnum.PENDING,
            "created_at": datetime.now(timezone.utc),
        }
        await target_db["kyc_applications"].insert_one(kyc_data)
        await target_db["users"].update_one({"_id": user_id}, {"$set": {"kyc_status": KYCStatusEnum.PENDING}})
        logger.info("User successfully uploaded identity verification documents to secure storage system")
        return {"status": "success", "message": "Identity verification documents securely uploaded and are pending review"}

    @staticmethod
    async def get_public_profile(slug: str, db=None) -> dict:
        target_db = db or db_client.mongodb.get_default_database()
        author = await target_db["users"].find_one(
            {"$or": [{"slug": slug}, {"username": slug}, {"_id": slug}], "is_active": {"$ne": False}}
        )
        if not author:
            raise HTTPException(status_code=404, detail="Requested public member profile could not be located within system records")
            
        creator_id = str(author["_id"])
        docs = await target_db["documents"].find({"creator_id": creator_id, "status": "PUBLISHED"}).sort("created_at", -1).limit(10).to_list(length=10)
        
        return {
            "_id": creator_id,
            "full_name": author.get("full_name", "Anonymous Member"),
            "slug": author.get("slug", ""),
            "role": author.get("role", "READER"),
            "avatar_url": author.get("avatar_url"),
            "bio": author.get("bio", ""),
            "cover_image_url": author.get("author_profile", {}).get("cover_image_url") or author.get("brand_page", {}).get("banner_url") or author.get("cover_url", ""),
            "welcome_video_url": author.get("author_profile", {}).get("welcome_video_url"),
            "custom_theme": author.get("author_profile", {}).get("custom_theme"),
            "followers_count": 0,
            "following_count": 0,
            "social_links": author.get("social_links", {}),
            "badges": author.get("badges", []),
            "wallet_address": author.get("wallet_address", ""),
            "recent_documents": [
                {
                    "_id": str(d["_id"]),
                    "title": d.get("title"),
                    "slug": d.get("slug"),
                    "cover_url": d.get("cover_url") or d.get("cover_image"),
                    "category_name": d.get("category_name", ""),
                    "views_count": d.get("views_count", 0),
                    "price_dl": d.get("price_dl", 0),
                }
                for d in docs
            ],
            "recent_posts": [],
        }