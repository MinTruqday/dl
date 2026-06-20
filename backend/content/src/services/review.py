import uuid
from datetime import datetime, timezone

from core.database import db_client
from core.repositories.base_repository import RepositoryFactory
from fastapi import HTTPException
from loguru import logger
from uuid6 import uuid7


class ReviewService:

    @staticmethod
    async def rate_document(document_id: str, rating_data, current_user, db=None):
        if db is None:
            db = db_client.mongodb.get_default_database()
        await RepositoryFactory.get("reviews").update_one(
            {"user_id": str(current_user.id), "document_id": document_id},
            {
                "$set": {
                    "rating": rating_data.rating,
                    "review_text": rating_data.review_text,
                    "created_at": datetime.now(timezone.utc),
                }
            },
            upsert=True,
        )
        logger.info("Đã gửi đánh giá tài liệu")
        return {"status": "success"}

    @staticmethod
    async def report_typo(document_id: str, data, current_user, db=None) -> dict:
        if db is None:
            db = db_client.mongodb.get_default_database()
        text_excerpt = (
            getattr(data, "text_excerpt", None)
            or getattr(data, "selected_text", "")
            or ""
        )
        description = (
            getattr(data, "description", None)
            or getattr(data, "context_text", "")
            or ""
        )
        report = {
            "_id": str(uuid7()),
            "user_id": str(current_user.id),
            "document_id": document_id,
            "text_excerpt": text_excerpt[:500] if text_excerpt else "",
            "description": description[:300] if description else "",
            "status": "pending",
            "created_at": datetime.now(timezone.utc),
        }
        await RepositoryFactory.get("typo_reports").insert_one(report)
        logger.info(
            "Ghi nhận báo cáo lỗi chính tả thành công"
        )
        return {"message": "Ghi nhận đóng góp cộng tác thành công"}

    @staticmethod
    async def get_typo_reports(document_id: str, current_user, db=None) -> list:
        if db is None:
            db = db_client.mongodb.get_default_database()
        reports = (
            await RepositoryFactory.get("typo_reports")
            .find({"document_id": document_id, "user_id": str(current_user.id)})
            .sort("created_at", -1)
            .to_list(length=50)
        )
        return [
            {
                "_id": str(r["_id"]),
                "text_excerpt": r.get("text_excerpt", ""),
                "description": r.get("description", ""),
                "status": r.get("status", "pending"),
                "created_at": (
                    r["created_at"].isoformat()
                    if isinstance(r.get("created_at"), datetime)
                    else ""
                ),
            }
            for r in reports
        ]

    @staticmethod
    async def create_review(document_id: str, review_in, current_user, db=None) -> dict:
        if db is None:
            db = db_client.mongodb.get_default_database()
        content_text = (
            getattr(review_in, "content", None)
            or getattr(review_in, "comment", "")
            or ""
        )
        review_item = {
            "_id": str(uuid7()),
            "document_id": document_id,
            "user_id": str(current_user.id),
            "full_name": current_user.full_name or "Anonymous collaborator",
            "avatar_url": getattr(current_user, "avatar_url", None),
            "rating": review_in.rating,
            "content": content_text,
            "comment": content_text,
            "created_at": datetime.now(timezone.utc),
        }
        await RepositoryFactory.get("reviews").update_one(
            {"user_id": str(current_user.id), "document_id": document_id},
            {"$set": review_item},
            upsert=True,
        )
        logger.info(
            "Thêm đánh giá và xếp hạng tài liệu thành công"
        )
        return review_item

    @staticmethod
    async def get_reviews(document_id: str, db=None) -> list:
        if db is None:
            db = db_client.mongodb.get_default_database()
        reviews = (
            await RepositoryFactory.get("reviews")
            .find({"document_id": document_id})
            .sort("created_at", -1)
            .to_list(length=100)
        )
        for r in reviews:
            r["_id"] = str(r["_id"])
            r["comment"] = r.get("content", "")
        return reviews

    @staticmethod
    async def get_document_reviews(document_id: str, db=None) -> list:
        return await ReviewService.get_reviews(document_id)

    @staticmethod
    async def report_content(data, current_user, db=None) -> dict:
        if db is None:
            db = db_client.mongodb.get_default_database()
        item_type = (
            getattr(data, "item_type", None) or getattr(data, "target_type", "") or ""
        )
        item_id = getattr(data, "item_id", None) or getattr(data, "target_id", "") or ""
        description = (
            getattr(data, "description", None) or getattr(data, "details", "") or ""
        )
        report = {
            "_id": str(uuid7()),
            "reporter_id": str(current_user.id),
            "item_type": item_type,
            "item_id": item_id,
            "reason": data.reason,
            "description": description,
            "status": "pending",
            "created_at": datetime.now(timezone.utc),
        }
        await RepositoryFactory.get("reports").insert_one(report)
        logger.info("Ghi nhận báo cáo vi phạm thành công")
        return {"message": "Gửi báo cáo vi phạm thành công"}