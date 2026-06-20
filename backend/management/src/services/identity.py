import uuid
from datetime import datetime, timezone

from fastapi import HTTPException
from loguru import logger
from uuid6 import uuid7

from core.database import db_client
from core.schemas.user import CreatorStatusEnum, KYCStatusEnum, RoleEnum
from core.storage import upload_file


class IdentityService:

    @staticmethod
    async def become_author(current_user, db=None):
        if db is None:
            db = db_client.mongodb.get_default_database()
        user_id = str(current_user.id)
        if current_user.role != RoleEnum.READER:
            raise HTTPException(
                status_code=400,
                detail="Chỉ tài khoản độc giả mới có thể nâng cấp",
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
        logger.info("Nâng cấp quyền tác giả thành công")
        return {"status": "success", "message": "Đã nâng cấp tài khoản tác giả"}

    @staticmethod
    async def apply_author(application, current_user, db=None):
        if db is None:
            db = db_client.mongodb.get_default_database()
        user_id = str(current_user.id)
        if current_user.role == RoleEnum.AUTHOR:
            raise HTTPException(status_code=400, detail="Tài khoản đã có quyền tác giả")
        if current_user.role != RoleEnum.READER:
            raise HTTPException(
                status_code=403,
                detail="Chỉ tài khoản người đọc mới có thể đăng ký tác giả",
            )
        if current_user.creator_status == CreatorStatusEnum.PENDING:
            raise HTTPException(
                status_code=400,
                detail="Yêu cầu nâng cấp tác giả đang được xét duyệt",
            )
        if current_user.creator_status == CreatorStatusEnum.SUSPENDED:
            raise HTTPException(
                status_code=403,
                detail="Tài khoản bị hạn chế nâng cấp tác giả",
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
        logger.info("Gửi yêu cầu nâng cấp tác giả thành công")
        return {"status": "success", "message": "Đã gửi yêu cầu nâng cấp tác giả"}

    @staticmethod
    async def upload_kyc(file, current_user, db=None):
        if db is None:
            db = db_client.mongodb.get_default_database()
        user_id = str(current_user.id)
        if current_user.kyc_status == KYCStatusEnum.PENDING:
            raise HTTPException(
                status_code=400,
                detail="Tài liệu xác minh danh tính đang được xét duyệt",
            )
        if current_user.kyc_status == KYCStatusEnum.VERIFIED:
            raise HTTPException(status_code=400, detail="Tài khoản đã được xác minh")
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
        logger.info("Tải lên tài liệu xác minh thành công")
        return {
            "status": "success",
            "message": "Tài liệu xác minh danh tính đang chờ xét duyệt",
        }

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
                status_code=404, detail="Không tìm thấy hồ sơ công khai"
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
