from datetime import datetime, timezone
import uuid
from uuid6 import uuid7
from fastapi import HTTPException
from core.database import db_client
from core.schemas.user import CreatorStatusEnum, KYCStatusEnum, RoleEnum
from core.storage import upload_file
from loguru import logger


class IdentityService:

    @staticmethod
    async def become_author(current_user, db=None):
        if db is None:
            db = db_client.mongodb.get_default_database()
        user_id = str(current_user.id)
        if current_user.role != RoleEnum.READER:
            raise HTTPException(
                status_code=400,
                detail="This action is restricted because only accounts with standard reader privileges are permitted to initiate an upgrade to author status",
            )
        await db["users"].update_one(
            {"_id": user_id},
            {
                "$set": {
                    "role": RoleEnum.AUTHOR,
                    "updated_at": datetime.now(timezone.utc),
                }
            },
        )
        logger.info("The access privileges for the specified user account have been successfully elevated to the author role level")
        return {"status": "success", "message": "Your account has been successfully upgraded and granted full author publishing privileges"}

    @staticmethod
    async def apply_author(application, current_user, db=None):
        if db is None:
            db = db_client.mongodb.get_default_database()
        user_id = str(current_user.id)
        if current_user.role == RoleEnum.AUTHOR:
            raise HTTPException(status_code=400, detail="The specified account is already configured with full author privileges and capabilities")
        if current_user.role != RoleEnum.READER:
            raise HTTPException(
                status_code=403, detail="This action is restricted because only accounts with standard reader privileges are permitted to submit an author application"
            )
        if current_user.creator_status == CreatorStatusEnum.PENDING:
            raise HTTPException(
                status_code=400,
                detail="Your previous application for author status is currently under active administrative review",
            )
        if current_user.creator_status == CreatorStatusEnum.SUSPENDED:
            raise HTTPException(
                status_code=403,
                detail="Your account is currently restricted by the administration and cannot apply for elevated author privileges",
            )
        application_data = {
            "_id": str(uuid7()),
            "user_id": user_id,
            "portfolio_url": (
                application.get("portfolio_url", "")
                if isinstance(application, dict)
                else ""
            ),
            "reason": (
                application.get("reason", "")
                if isinstance(application, dict)
                else application if isinstance(application, str) else ""
            ),
            "status": CreatorStatusEnum.PENDING,
            "created_at": datetime.now(timezone.utc),
        }
        await db["author_applications"].insert_one(application_data)
        await db["users"].update_one(
            {"_id": user_id},
            {
                "$set": {
                    "creator_status": CreatorStatusEnum.PENDING,
                    "tos_accepted_at": datetime.now(timezone.utc),
                }
            },
        )
        logger.info("A new application for author privileges has been successfully submitted and recorded in the system pending review queue")
        return {"status": "success", "message": "Your author application has been submitted successfully and is awaiting administrative review"}

    @staticmethod
    async def upload_kyc(file, current_user, db=None):
        if db is None:
            db = db_client.mongodb.get_default_database()
        user_id = str(current_user.id)
        if current_user.kyc_status == KYCStatusEnum.PENDING:
            raise HTTPException(
                status_code=400, detail="Your submitted identity verification documents are currently under active administrative review"
            )
        if current_user.kyc_status == KYCStatusEnum.VERIFIED:
            raise HTTPException(
                status_code=400, detail="Your account identity has already been successfully verified by the system administration"
            )
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
        await db["kyc_applications"].insert_one(kyc_data)
        await db["users"].update_one(
            {"_id": user_id}, {"$set": {"kyc_status": KYCStatusEnum.PENDING}}
        )
        logger.info("The user has successfully uploaded their identity verification documents to the secure storage system")
        return {"status": "success", "message": "Your identity verification documents have been securely uploaded and are pending review"}

    @staticmethod
    async def get_public_profile(slug: str, db=None) -> dict:
        if db is None:
            db = db_client.mongodb.get_default_database()
        author = await db["users"].find_one(
            {
                "$or": [{"slug": slug}, {"username": slug}, {"_id": slug}],
                "is_active": {"$ne": False},
            }
        )
        if not author:
            raise HTTPException(
                status_code=404, detail="The requested public member profile could not be located within the system records"
            )
        creator_id = str(author["_id"])
        docs = (
            await db["documents"]
            .find({"creator_id": creator_id, "status": "PUBLISHED"})
            .sort("created_at", -1)
            .limit(10)
            .to_list(length=10)
        )
        return {
            "_id": creator_id,
            "full_name": author.get("full_name", "Anonymous Member"),
            "slug": author.get("slug", ""),
            "role": author.get("role", "READER"),
            "avatar_url": author.get("avatar_url"),
            "bio": author.get("bio", ""),
            "cover_image_url": author.get("author_profile", {}).get("cover_image_url")
            or author.get("brand_page", {}).get("banner_url")
            or author.get("cover_url", ""),
            "welcome_video_url": author.get("author_profile", {}).get(
                "welcome_video_url"
            ),
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