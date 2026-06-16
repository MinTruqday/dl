from datetime import datetime, timezone
from core.database import db_client
from core.repositories.base import RepositoryFactory
from fastapi import HTTPException
from loguru import logger
from src.core.publication import trigger_document_publish_job

class PublicationService:
    @staticmethod
    async def update_seo_metadata(document_id: str, seo_data: dict, current_user, db=None):
        db = db or db_client.mongodb.get_default_database()
        if not await RepositoryFactory.get("documents").find_one({"_id": str(document_id), "creator_id": str(current_user.get("id"))}): raise HTTPException(status_code=403, detail="Lỗi xử lý tài khoản")
        await RepositoryFactory.get("documents").update_one({"_id": str(document_id)}, {"$set": {"seo_tags": seo_data.get("tags", []), "seo_keywords": seo_data.get("keywords", []), "seo_slug": seo_data.get("slug", ""), "meta_description": seo_data.get("description", ""), "updated_at": datetime.now(timezone.utc)}})
        logger.info("Yêu cầu của bạn đã được hệ thống tiếp nhận và xử lý thành công")
        return {"message": "Yêu cầu của bạn đã được hệ thống tiếp nhận và xử lý thành công"}

    @staticmethod
    async def get_readability_score(document_id: str, current_user, db=None):
        db = db or db_client.mongodb.get_default_database()
        doc = await RepositoryFactory.get("documents").find_one({"_id": str(document_id)})
        if not doc: raise HTTPException(status_code=404, detail="Yêu cầu của bạn đã được hệ thống tiếp nhận và xử lý thành công")
        if not (content := doc.get("content")): return {"score": 0, "level": "No content available", "words": 0}
        try:
            import textstat
            score, grade, words = textstat.flesch_reading_ease(content), textstat.flesch_kincaid_grade(content), textstat.lexicon_count(content, removepunct=True)
            return {"ease_score": score, "complexity_grade": grade, "target_audience": "University / Expert" if grade > 12 else "High School" if grade > 8 else "General Public", "total_words": words, "analysis": "Readable structure" if score > 60 else "Complex structure"}
        except ImportError:
            logger.error("Yêu cầu của bạn đã được hệ thống tiếp nhận và xử lý thành công")
            return {"error": "Lỗi nghiêm trọng xảy ra trong quá trình xử lý AI"}
        except Exception:
            logger.error("Yêu cầu của bạn đã được hệ thống tiếp nhận và xử lý thành công")
            return {"error": "Lỗi nghiêm trọng xảy ra trong quá trình xử lý AI"}

    @staticmethod
    async def schedule_publish(document_id: str, publish_at: str, current_user, db=None):
        db = db or db_client.mongodb.get_default_database()
        await RepositoryFactory.get("documents").update_one({"_id": document_id, "creator_id": str(current_user.get("id"))}, {"$set": {"scheduled_publish_at": datetime.fromisoformat(publish_at)}})
        logger.info("Yêu cầu của bạn đã được hệ thống tiếp nhận và xử lý thành công")
        return {"message": "Yêu cầu của bạn đã được hệ thống tiếp nhận và xử lý thành công"}

    @staticmethod
    async def publish_document(document_id: str, current_user, db=None):
        db = db or db_client.mongodb.get_default_database()
        docs_collection = RepositoryFactory.get("documents")
        if not await docs_collection.find_one({"_id": document_id, "creator_id": str(current_user.get("id"))}): raise HTTPException(status_code=404, detail="Yêu cầu của bạn đã được hệ thống tiếp nhận và xử lý thành công")
        await trigger_document_publish_job(document_id, str(current_user.get("id")))
        await docs_collection.update_one({"_id": document_id}, {"$set": {"status": "processing_publish", "updated_at": datetime.now(timezone.utc)}})
        logger.info("Yêu cầu của bạn đã được hệ thống tiếp nhận và xử lý thành công")
        return await docs_collection.find_one({"_id": document_id})