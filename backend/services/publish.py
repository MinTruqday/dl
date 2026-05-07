from core.database import db_client
from fastapi import HTTPException
from datetime import datetime
from loguru import logger

class PublisherService:
    @staticmethod
    async def update_seo_metadata(document_id: str, seo_data: dict, current_user):
        db = db_client.mongodb.get_default_database()
        user_id = str(current_user.id)
        doc = await db["documents"].find_one({
            "_id": str(document_id), 
            "author_id": user_id
        })
        if not doc:
            raise HTTPException(status_code=403, detail="Không tìm thấy tài liệu hoặc bạn không có quyền truy cập.")
            
        await db["documents"].update_one({"_id": str(document_id)}, {"$set": {
            "seo_tags": seo_data.get("tags", []),
            "seo_keywords": seo_data.get("keywords", []),
            "seo_slug": seo_data.get("slug", ""),
            "meta_description": seo_data.get("description", ""),
            "updated_at": datetime.utcnow()
        }})
        
        logger.info(f"SEO metadata updated for document {document_id} by user {user_id}")
        return {"message": "Đã cập nhật thông tin thành công."}

    @staticmethod
    async def get_readability_score(document_id: str, current_user):
        db = db_client.mongodb.get_default_database()
        doc = await db["documents"].find_one({"_id": str(document_id)})
        if not doc:
            raise HTTPException(status_code=404, detail="Tài liệu không tồn tại.")
            
        content = doc.get("content")
        if not content:
            return {"score": 0, "level": "Chưa có nội dung", "words": 0}
            
        try:
            import textstat
            score = textstat.flesch_reading_ease(content)
            grade = textstat.flesch_kincaid_grade(content)
            words = textstat.lexicon_count(content, removepunct=True)
            
            target = "Đại học / Chuyên gia" if grade > 12 else "Trung học phổ thông" if grade > 8 else "Phổ thông đại chúng"
            
            return {
                "ease_score": score,
                "complexity_grade": grade,
                "target_audience": target,
                "total_words": words,
                "analysis": "Cấu trúc dễ đọc, tiếp tục phát huy." if score > 60 else "Cấu trúc câu hơi dài và học thuật."
            }
        except ImportError:
            logger.error("textstat library not found")
            return {"error": "Tính năng phân tích độ đọc chưa khả dụng."}
        except Exception as e:
            logger.error(f"Readability analysis error: {e}")
            return {"error": "Lỗi trong quá trình phân tích nội dung."}

    @staticmethod
    async def schedule_publish(document_id: str, publish_at: str, current_user):
        db = db_client.mongodb.get_default_database()
        user_id = str(current_user.id)
        await db["documents"].update_one(
            {"_id": document_id, "author_id": user_id},
            {"$set": {"scheduled_publish_at": datetime.fromisoformat(publish_at)}}
        )
        logger.info(f"Document {document_id} scheduled for publish at {publish_at} by user {user_id}")
        return {"message": "Đã hẹn giờ xuất bản thành công."}

    @staticmethod
    async def config_premium(document_id: str, premium_chapters: list, current_user):
        db = db_client.mongodb.get_default_database()
        user_id = str(current_user.id)
        await db["documents"].update_one(
            {"_id": document_id, "author_id": user_id},
            {"$set": {"premium_chapters": premium_chapters}}
        )
        logger.info(f"Premium config updated for document {document_id} by user {user_id}")
        return {"message": "Đã thiết lập chương tính phí."}

    @staticmethod
    async def publish_document(document_id: str, current_user):
        db = db_client.mongodb.get_default_database()
        docs_collection = db["documents"]
        user_id = str(current_user.id)
        document = await docs_collection.find_one({"_id": document_id, "author_id": user_id})
        if not document:
            raise HTTPException(status_code=404, detail="Không tìm thấy thông tin tài liệu.")
            
        from core.publisher import trigger_document_publish_job
        from services.rag import RagService
        
        await trigger_document_publish_job(document_id, user_id)
        try:
            await RagService.ingest(document_id)
        except Exception as e:
            logger.error(f"RAG: Ingestion failed for {document_id}: {e}")
            
        await docs_collection.update_one(
            {"_id": document_id},
            {"$set": {
                "status": "processing_publish",
                "updated_at": datetime.utcnow()
            }}
        )
        logger.info(f"Workspace: Document publishing triggered {document_id}")
        return await docs_collection.find_one({"_id": document_id})