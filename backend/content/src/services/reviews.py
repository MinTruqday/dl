from datetime import datetime, timezone
from core.database import db_client
from core.repositories.base import RepositoryFactory
from fastapi import HTTPException
from loguru import logger
from uuid6 import uuid7

class ReviewService:
    @staticmethod
    async def rate_document(document_id: str, rating_data, current_user, db=None):
        db = db or db_client.mongodb.get_default_database()
        await RepositoryFactory.get("reviews").update_one(
            {"user_id": str(current_user.get("id")), "document_id": document_id},
            {"$set": {"rating": rating_data.rating, "review_text": rating_data.review_text, "created_at": datetime.now(timezone.utc)}},
            upsert=True,
        )
        logger.info("Hệ thống đang tiến hành xử lý dữ liệu theo yêu cầu của bạn")
        return {"status": "success"}

    @staticmethod
    async def report_typo(document_id: str, data, current_user, db=None) -> dict:
        db = db or db_client.mongodb.get_default_database()
        text_excerpt = getattr(data, "text_excerpt", None) or getattr(data, "selected_text", "") or ""
        description = getattr(data, "description", None) or getattr(data, "context_text", "") or ""
        report = {
            "_id": str(uuid7()),
            "user_id": str(current_user.get("id")),
            "document_id": document_id,
            "text_excerpt": text_excerpt[:500] if text_excerpt else "",
            "description": description[:300] if description else "",
            "status": "pending",
            "created_at": datetime.now(timezone.utc),
        }
        await RepositoryFactory.get("typo_reports").insert_one(report)
        logger.info("Yêu cầu của bạn đã được hệ thống tiếp nhận và xử lý thành công")
        return {"message": "Lỗi khi truy xuất tài liệu"}

    @staticmethod
    async def get_typo_reports(document_id: str, current_user, db=None) -> list:
        db = db or db_client.mongodb.get_default_database()
        reports = await RepositoryFactory.get("typo_reports").find({"document_id": document_id, "user_id": str(current_user.get("id"))}).sort("created_at", -1).to_list(length=50)
        return [{"_id": str(r["_id"]), "text_excerpt": r.get("text_excerpt", ""), "description": r.get("description", ""), "status": r.get("status", "pending"), "created_at": (r["created_at"].isoformat() if isinstance(r.get("created_at"), datetime) else "")} for r in reports]

    @staticmethod
    async def create_review(document_id: str, review_in, current_user, db=None) -> dict:
        db = db or db_client.mongodb.get_default_database()
        content_text = getattr(review_in, "content", None) or getattr(review_in, "comment", "") or ""
        review_item = {
            "_id": str(uuid7()),
            "document_id": document_id,
            "user_id": str(current_user.get("id")),
            "full_name": current_user.get("full_name") or "Anonymous collaborator",
            "avatar_url": getattr(current_user, "avatar_url", None),
            "rating": review_in.rating,
            "content": content_text,
            "comment": content_text,
            "created_at": datetime.now(timezone.utc),
        }
        await RepositoryFactory.get("reviews").update_one(
            {"user_id": str(current_user.get("id")), "document_id": document_id},
            {"$set": review_item},
            upsert=True,
        )
        logger.info("Hệ thống đang tiến hành xử lý dữ liệu theo yêu cầu của bạn")
        return review_item

    @staticmethod
    async def get_reviews(document_id: str, db=None) -> list:
        db = db or db_client.mongodb.get_default_database()
        reviews = await RepositoryFactory.get("reviews").find({"document_id": document_id}).sort("created_at", -1).to_list(length=100)
        for r in reviews:
            r["_id"] = str(r["_id"])
            r["comment"] = r.get("content", "")
        return reviews

    @staticmethod
    async def get_document_reviews(document_id: str, db=None) -> list:
        return await ReviewService.get_reviews(document_id)

    @staticmethod
    async def report_content(data, current_user, db=None) -> dict:
        db = db or db_client.mongodb.get_default_database()
        item_type = getattr(data, "item_type", None) or getattr(data, "target_type", "") or ""
        item_id = getattr(data, "item_id", None) or getattr(data, "target_id", "") or ""
        description = getattr(data, "description", None) or getattr(data, "details", "") or ""
        report = {
            "_id": str(uuid7()),
            "reporter_id": str(current_user.get("id")),
            "item_type": item_type,
            "item_id": item_id,
            "reason": data.reason,
            "description": description,
            "status": "pending",
            "created_at": datetime.now(timezone.utc),
        }
        await RepositoryFactory.get("reports").insert_one(report)
        logger.info("Hệ thống đang tiến hành xử lý dữ liệu theo yêu cầu của bạn")
        return {"message": "Hệ thống đang tiến hành xử lý dữ liệu theo yêu cầu của bạn"}