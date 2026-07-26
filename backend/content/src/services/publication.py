from src.core.logic_logger import log_logic_execution
from datetime import datetime, timezone

from fastapi import HTTPException
from loguru import logger
from uuid6 import uuid7

from src.repositories.document import DocumentRepository
from src.services.document import DocumentService

class PublicationService:

    @staticmethod
    @log_logic_execution
    async def update_seo_metadata(
        document_id: str, seo_data: dict, current_user
    ):
        user_id = str(current_user.id)
        doc = await DocumentRepository.find_one(
            {"_id": str(document_id), "creator_id": user_id}
        )
        if not doc:
            raise HTTPException(
                status_code=403,
                detail="Hệ thống không tìm thấy tài liệu yêu cầu hoặc bạn không có quyền truy cập",
            )
        await DocumentRepository.update_one(
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
        logger.info("Document SEO metadata updated successfully")
        return {"message": "Cập nhật dữ liệu SEO và thẻ phân loại hoàn tất"}

    @staticmethod
    @log_logic_execution
    async def get_readability_score(document_id: str, current_user):
        doc = await DocumentRepository.find_one(
            {"_id": str(document_id)}
        )
        if not doc:
            raise HTTPException(status_code=404, detail="Hệ thống không tìm thấy tài liệu yêu cầu")
        if doc.get("creator_id") != str(current_user.id) and not DocumentService._is_admin(current_user) and doc.get("status") != "published":
            raise HTTPException(status_code=403, detail="Bạn không có quyền phân tích tài liệu này")
        content = doc.get("content")
        if not content:
            return {"score": 0, "level": "No content available", "words": 0}
        import re

        words_list = re.findall(r"[\wÀ-ỹ]+", str(content), flags=re.UNICODE)
        words = len(words_list)
        sentences = max(1, len(re.findall(r"[.!?]+", str(content))))
        vowels = "aeiouyàáảãạăằắẳẵặâầấẩẫậèéẻẽẹêềếểễệìíỉĩịòóỏõọôồốổỗộơờớởỡợùúủũụưừứửữựỳýỷỹỵ"
        syllables = 0
        for word in words_list:
            groups = re.findall(f"[{vowels}]+", word.lower())
            syllables += max(1, len(groups))
        ease = 206.835 - 1.015 * (words / sentences) - 84.6 * (syllables / max(words, 1))
        grade = 0.39 * (words / sentences) + 11.8 * (syllables / max(words, 1)) - 15.59
        score = round(max(0, min(100, ease)), 1)
        grade = round(max(0, grade), 1)
        target = "University / Expert" if grade > 12 else "High School" if grade > 8 else "General Public"
        return {
            "ease_score": score,
            "complexity_grade": grade,
            "target_audience": target,
            "total_words": words,
            "analysis": "Readable structure" if score > 60 else "Complex structure",
        }

    @staticmethod
    @log_logic_execution
    async def schedule_publish(
        document_id: str, publish_at: str, current_user
    ):
        user_id = str(current_user.id)
        result = await DocumentRepository.update_one(
            {"_id": document_id, "creator_id": user_id},
            {"$set": {"scheduled_publish_at": datetime.fromisoformat(publish_at) if isinstance(publish_at, str) else publish_at}},
        )
        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="Hệ thống không tìm thấy tài liệu cần lên lịch")
        logger.info("Document publication schedule configured successfully")
        return {"message": "Thiết lập lịch trình xuất bản tự động hoàn tất"}

    @staticmethod
    @log_logic_execution
    async def publish_document(document_id: str, current_user):
        docs_collection = DocumentRepository
        user_id = str(current_user.id)
        document = await docs_collection.find_one(
            {"_id": document_id, "creator_id": user_id}
        )
        if not document:
            raise HTTPException(status_code=404, detail="Hệ thống không tìm thấy tài liệu yêu cầu")
        from src.core.publication import trigger_document_publish_job

        job_id = f"publish-{uuid7()}"
        now = datetime.now(timezone.utc)
        claimed = await docs_collection.update_one(
            {
                "_id": document_id,
                "creator_id": user_id,
                "status": {"$nin": ["processing_publish", "published"]},
                "is_deleted": {"$ne": True},
            },
            {
                "$set": {
                    "status": "processing_publish",
                    "publication_job_id": job_id,
                    "updated_at": now,
                },
                "$unset": {"publication_error": ""},
            },
        )
        if claimed.modified_count != 1:
            raise HTTPException(status_code=409, detail="Tài liệu không thể chuyển sang trạng thái xuất bản")
        queued = await trigger_document_publish_job(document_id, user_id, job_id)
        if not queued:
            await docs_collection.update_one(
                {"_id": document_id, "publication_job_id": job_id},
                {
                    "$set": {"status": "draft", "updated_at": datetime.now(timezone.utc)},
                    "$unset": {"publication_job_id": ""},
                },
            )
            raise HTTPException(status_code=503, detail="Hàng đợi xuất bản tạm thời không khả dụng")
        logger.info("Document publication process initiated successfully")
        return await docs_collection.find_one({"_id": document_id})
