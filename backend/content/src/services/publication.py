from datetime import datetime, timezone

from fastapi import HTTPException
from loguru import logger

from shared.infrastructure.database import database
from shared.repositories.database import BaseRepository


class PublicationService:

    @staticmethod
    async def update_seo_metadata(
        document_id: str, seo_data: dict, current_user, db=None
    ):
        if db is None:
            db = database.mongodb.get_default_database()
        user_id = str(current_user.id)
        doc = await BaseRepository.get("documents").find_one(
            {"_id": str(document_id), "creator_id": user_id}
        )
        if not doc:
            raise HTTPException(
                status_code=403,
                detail="Không tìm thấy tài liệu hoặc không có quyền truy cập",
            )
        await BaseRepository.get("documents").update_one(
            {"_id": str(document_id)},
            {
                "$set": {
                    "seo_tags": seo_data.get("tags", []),
                    "seo_keywords": seo_data.get("keywords", []),
                    "seo_slug": seo_data.get("slug", ""),
                    "meta_description": seo_data.get("description", ""),
                    "updated_at": datetime.now(timezone.utc),
                }
            },
        )
        logger.info("Chỉnh sửa thông tin SEO thành công")
        return {"message": "Cập nhật thông tin và thẻ phân loại thành công"}

    @staticmethod
    async def get_readability_score(document_id: str, current_user, db=None):
        if db is None:
            db = database.mongodb.get_default_database()
        doc = await BaseRepository.get("documents").find_one(
            {"_id": str(document_id)}
        )
        if not doc:
            raise HTTPException(status_code=404, detail="Hệ thống không thể tìm thấy tài liệu theo yêu cầu của bạn")
        content = doc.get("content")
        if not content:
            return {"score": 0, "level": "No content available", "words": 0}
        try:
            import textstat

            score = textstat.flesch_reading_ease(content)
            grade = textstat.flesch_kincaid_grade(content)
            words = textstat.lexicon_count(content, removepunct=True)
            target = (
                "University / Expert"
                if grade > 12
                else "High School" if grade > 8 else "General Public"
            )
            return {
                "ease_score": score,
                "complexity_grade": grade,
                "target_audience": target,
                "total_words": words,
                "analysis": "Readable structure" if score > 60 else "Complex structure",
            }
        except ImportError as e:
            logger.error(f"Lỗi phân tích ngôn ngữ: {e}")
            return {"error": f"Đánh giá khả năng đọc đang bảo trì: {e}"}
        except Exception as e:
            logger.error(f"Lỗi phân tích cấu trúc tài liệu: {e}")
            return {"error": f"Lỗi phân tích ngôn ngữ do định dạng không xác định: {e}"}

    @staticmethod
    async def schedule_publish(
        document_id: str, publish_at: str, current_user, db=None
    ):
        if db is None:
            db = database.mongodb.get_default_database()
        user_id = str(current_user.id)
        await BaseRepository.get("documents").update_one(
            {"_id": document_id, "creator_id": user_id},
            {"$set": {"scheduled_publish_at": datetime.fromisoformat(publish_at) if isinstance(publish_at, str) else publish_at}},
        )
        logger.info("Cấu hình lịch xuất bản tài liệu thành công")
        return {"message": "Ghi nhận lịch xuất bản thành công"}

    @staticmethod
    async def publish_document(document_id: str, current_user, db=None):
        if db is None:
            db = database.mongodb.get_default_database()
        docs_collection = BaseRepository.get("documents")
        user_id = str(current_user.id)
        document = await docs_collection.find_one(
            {"_id": document_id, "creator_id": user_id}
        )
        if not document:
            raise HTTPException(status_code=404, detail="Hệ thống không thể tìm thấy tài liệu theo yêu cầu của bạn")
        from src.core.publication import trigger_document_publish_job

        await trigger_document_publish_job(document_id, user_id)
        await docs_collection.update_one(
            {"_id": document_id},
            {
                "$set": {
                    "status": "processing_publish",
                    "updated_at": datetime.now(timezone.utc),
                }
            },
        )
        logger.info("Đã bắt đầu quy trình xuất bản")
        return await docs_collection.find_one({"_id": document_id})
