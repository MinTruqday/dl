from datetime import datetime, timezone
import uuid
from uuid6 import uuid7
from fastapi import HTTPException
from core.database import db_client
from core.schemas.user import AuthorStatusEnum, KYCStatusEnum, RoleEnum
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
                detail="Chỉ có độc giả mới có thể nâng cấp trực tiếp lên tác giả",
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
        logger.info(f"Identity: User {user_id} upgraded to AUTHOR role directly")
        return {"status": "success", "message": "Đã nâng cấp thành tác giả"}

    @staticmethod
    async def apply_author(application, current_user, db=None):
        if db is None:
            db = db_client.mongodb.get_default_database()
        user_id = str(current_user.id)
        if current_user.role == RoleEnum.AUTHOR:
            raise HTTPException(status_code=400, detail="Bạn đã là tác giả")
        if current_user.role != RoleEnum.READER:
            raise HTTPException(
                status_code=403, detail="Chỉ độc giả mới có thể đăng ký làm tác giả"
            )
        if current_user.author_status == AuthorStatusEnum.PENDING:
            raise HTTPException(
                status_code=400,
                detail="Yêu cầu đăng ký làm tác giả của bạn đang được xét duyệt",
            )
        if current_user.author_status == AuthorStatusEnum.SUSPENDED:
            raise HTTPException(
                status_code=403,
                detail="Tài khoản của bạn đã bị khóa quyền đăng ký làm tác giả",
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
            "status": AuthorStatusEnum.PENDING,
            "created_at": datetime.now(timezone.utc),
        }
        await db["author_applications"].insert_one(application_data)
        await db["users"].update_one(
            {"_id": user_id},
            {
                "$set": {
                    "author_status": AuthorStatusEnum.PENDING,
                    "tos_accepted_at": datetime.now(timezone.utc),
                }
            },
        )
        logger.info(f"Identity: Reader {user_id} requested author status")
        return {"status": "success", "message": "Đã gửi yêu cầu đăng ký tác giả"}

    @staticmethod
    async def upload_kyc(file, current_user, db=None):
        if db is None:
            db = db_client.mongodb.get_default_database()
        user_id = str(current_user.id)
        if current_user.kyc_status == KYCStatusEnum.PENDING:
            raise HTTPException(
                status_code=400, detail="Tài liệu KYC đang được xem xét"
            )
        if current_user.kyc_status == KYCStatusEnum.VERIFIED:
            raise HTTPException(
                status_code=400, detail="Tài khoản đã được xác minh KYC"
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
        logger.info(f"Identity: User {user_id} uploaded KYC documents")
        return {"status": "success", "message": "Đã tải lên tài liệu KYC"}

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
                status_code=404, detail="Không tìm thấy trang thành viên"
            )
        author_id = str(author["_id"])
        docs = (
            await db["documents"]
            .find({"author_id": author_id, "status": "PUBLISHED"})
            .sort("created_at", -1)
            .limit(10)
            .to_list(length=10)
        )
        return {
            "_id": author_id,
            "full_name": author.get("full_name", "Ẩn danh"),
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
