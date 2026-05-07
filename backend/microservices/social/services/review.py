from core.database import db_client
from fastapi import HTTPException
from datetime import datetime
import uuid
from loguru import logger
class ReviewService:
    @staticmethod
    async def rate_document(document_id: str, rating_data, current_user):
        db = db_client.mongodb.get_default_database()
        await db["reviews"].update_one(
            {"user_id": str(current_user.id), "document_id": document_id}, 
            {"$set": {
                "rating": rating_data.rating, 
                "review_text": rating_data.review_text, 
                "created_at": datetime.utcnow()
            }}, 
            upsert=True
        )
        logger.info(f"Feedback: Document {document_id} rated {rating_data.rating} by {current_user.id}")
        return {"status": "success"}
    @staticmethod
    async def rate_chapter(document_id: str, data, current_user) -> dict:
        db = db_client.mongodb.get_default_database()
        if data.rating < 1 or data.rating > 5:
            raise HTTPException(status_code=400, detail="Điểm đánh giá phải từ 1 đến 5.")
        await db["chapter_ratings"].update_one(
            {"user_id": str(current_user.id), "document_id": document_id, "chapter_slug": data.chapter_slug},
            {"$set": {"rating": data.rating, "updated_at": datetime.utcnow()}},
            upsert=True,
        )
        logger.info(f"Feedback: Chapter {data.chapter_slug} rated {data.rating} by {current_user.id}")
        return {"message": "Đã ghi nhận đánh giá chương của bạn."}
    @staticmethod
    async def report_typo(document_id: str, data, current_user) -> dict:
        db = db_client.mongodb.get_default_database()
        report = {
            "_id": str(uuid.uuid4()),
            "user_id": str(current_user.id),
            "document_id": document_id,
            "chapter_slug": data.chapter_slug,
            "text_excerpt": data.text_excerpt[:500],
            "description": data.description[:300],
            "status": "pending",
            "created_at": datetime.utcnow(),
        }
        await db["typo_reports"].insert_one(report)
        logger.info(f"Feedback: Typo report submitted for {document_id} by {current_user.id}")
        return {"message": "Đã gửi báo cáo lỗi chính tả thành công."}
    @staticmethod
    async def get_typo_reports(document_id: str, current_user) -> list:
        db = db_client.mongodb.get_default_database()
        reports = await db["typo_reports"].find(
            {"document_id": document_id, "user_id": str(current_user.id)}
        ).sort("created_at", -1).to_list(length=50)
        return [{
            "id": str(r["_id"]),
            "chapter_slug": r.get("chapter_slug", ""),
            "text_excerpt": r.get("text_excerpt", ""),
            "description": r.get("description", ""),
            "status": r.get("status", "pending"),
            "created_at": r["created_at"].isoformat() if isinstance(r.get("created_at"), datetime) else "",
        } for r in reports]
    @staticmethod
    async def get_document_reviews(document_id: str) -> list:
        db = db_client.mongodb.get_default_database()
        reviews = await db["reviews"].find({"document_id": document_id}).sort("created_at", -1).to_list(length=100)
        for r in reviews:
            r["_id"] = str(r["_id"])
        return reviews
    @staticmethod
    async def report_content(data, current_user) -> dict:
        db = db_client.mongodb.get_default_database()
        report = {
            "_id": str(uuid.uuid4()),
            "reporter_id": str(current_user.id),
            "item_type": data.item_type,
            "item_id": data.item_id,
            "reason": data.reason,
            "description": data.description,
            "status": "pending",
            "created_at": datetime.utcnow()
        }
        await db["reports"].insert_one(report)
        logger.info(f"Feedback: Content report submitted by {current_user.id} for {data.item_type} {data.item_id}")
        return {"message": "Đã gửi báo cáo nội dung thành công."}
