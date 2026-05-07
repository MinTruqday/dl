import uuid
import datetime
from fastapi import HTTPException
from shared.core.database import db_client
from loguru import logger
from utils.metric import calculate_flesch_kincaid, calculate_vocabulary_richness

def serialize_document(document):
    if not document:
        return None
    if "_id" in document:
        document["_id"] = str(document["_id"])
    if "created_at" not in document:
        document["created_at"] = datetime.datetime.utcnow()
    return document

class ChapterService:
    @staticmethod
    async def add_chapter(document_id: str, chapter_in, current_user):
        db = db_client.mongodb.get_default_database()
        docs_col = db["documents"]
        document = await docs_col.find_one({"_id": document_id})
        user_id = str(current_user.id)
        if not document or (document.get("author_id") != user_id and user_id not in document.get("coauthors", [])):
            raise HTTPException(status_code=403, detail="Không có quyền thêm chương.")
            
        order = len(document.get("chapters", [])) + 1
        new_chapter = {
            "id": str(uuid.uuid4()),
            "title": chapter_in.title,
            "content": chapter_in.content,
            "order": order,
            "is_premium": chapter_in.is_premium,
            "price_dl": chapter_in.price_dl,
            "words_count": len(chapter_in.content.split()),
            "readability_score": calculate_flesch_kincaid(chapter_in.content),
            "vocabulary_richness": calculate_vocabulary_richness(chapter_in.content),
            "created_at": datetime.datetime.utcnow()
        }
        await docs_col.update_one({"_id": document_id}, {"$push": {"chapters": new_chapter}})
logger.info("Log message sanitized"))
        return serialize_document(await docs_col.find_one({"_id": document_id}))

    @staticmethod
    async def set_free_preview(document_id: str, chapter_ids: list, current_user) -> dict:
        db = db_client.mongodb.get_default_database()
        doc = await db["documents"].find_one({"_id": document_id, "author_id": str(current_user.id)})
        if not doc:
            raise HTTPException(status_code=404, detail="Tài liệu không tồn tại.")
            
        chapters = doc.get("chapters", [])
        for ch in chapters:
            ch["is_premium"] = ch["id"] not in chapter_ids
            
        await db["documents"].update_one({"_id": document_id}, {"$set": {"chapters": chapters, "updated_at": datetime.datetime.utcnow()}})
logger.info("Log message sanitized"))
        return {"message": "Đã thiết lập chương đọc thử thành công."}

    @staticmethod
    async def get_document_dropoff(document_id: str, current_user) -> dict:
        db = db_client.mongodb.get_default_database()
        doc = await db["documents"].find_one({"_id": document_id, "author_id": str(current_user.id)})
        if not doc:
            raise HTTPException(status_code=404, detail="Không tìm thấy tài liệu.")
            
        chapters = doc.get("chapters", [])
        if not chapters:
            return {"chapters": [], "message": "Tài liệu chưa có chương nào."}
            
        dropoff_data = []
        base_readers = doc.get("views", 100)
        for i, ch in enumerate(chapters):
            readers = int(base_readers * (0.85 ** i))
            dropoff_data.append({
                "chapter_id": ch["id"],
                "chapter_title": ch.get("title", f"Chương {i+1}"),
                "readers_started": readers,
                "readers_completed": int(readers * 0.9),
                "dropoff_rate": round((readers - int(readers * 0.9)) / readers * 100, 2) if readers > 0 else 0
            })
            
        return {"document_id": document_id, "dropoff_data": dropoff_data}

    @staticmethod
    async def get_document_chapters(document_id: str, current_user):
        db = db_client.mongodb.get_default_database()
        doc = await db["documents"].find_one({"_id": document_id})
        if not doc:
            raise HTTPException(status_code=404, detail="Không tìm thấy tài liệu.")
            
        chapters = doc.get("chapters", [])
        return chapters
