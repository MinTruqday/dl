from core.database import db_client
from fastapi import HTTPException
from datetime import datetime, timedelta
from loguru import logger

class ReadService:
    @staticmethod
    async def update_typography(data: dict, current_user) -> dict:
        db = db_client.mongodb.get_default_database()
        allowed_fonts = ["Inter", "Roboto", "Outfit", "Noto Sans", "Source Sans Pro"]
        font = data.get("font_family", "Inter")
        if font not in allowed_fonts: 
            raise HTTPException(status_code=400, detail="Font chữ không được hỗ trợ.")
            
        update_data = {
            "font_family": font, 
            "font_size": max(12, min(28, data.get("font_size", 16))), 
            "line_height": max(1.2, min(3.0, data.get("line_height", 1.8))), 
            "letter_spacing": max(-0.5, min(2.0, data.get("letter_spacing", 0))), 
            "updated_at": datetime.utcnow()
        }
        await db["reading_preferences"].update_one({"user_id": str(current_user.id)}, {"$set": update_data}, upsert=True)
        return {"message": "Đã cập nhật tùy chỉnh kiểu chữ."}

    @staticmethod
    async def get_reading_history(current_user, skip: int = 0, limit: int = 20) -> list:
        db = db_client.mongodb.get_default_database()
        history = await db["reading_history"].find({"user_id": str(current_user.id)}).sort("last_read_at", -1).skip(skip).limit(limit).to_list(length=limit)
        result = []
        for h in history:
            doc = await db["documents"].find_one({"_id": h["document_id"]}, {"title": 1, "slug": 1, "cover_url": 1, "author_id": 1})
            if doc:
                author_name = "Hệ thống DocLib"
                author = await db["users"].find_one({"_id": doc.get("author_id")}, {"full_name": 1})
                if author:
                    author_name = author.get("full_name") or author_name
                
                result.append({
                    "document_id": h["document_id"], 
                    "document_title": doc.get("title", ""), 
                    "document_slug": doc.get("slug", ""), 
                    "author_name": author_name,
                    "cover_url": doc.get("cover_url"), 
                    "progress_percentage": h.get("progress_percentage", 0), 
                    "last_read_at": h["last_read_at"].isoformat() if isinstance(h.get("last_read_at"), datetime) else ""
                })
        return result

    @staticmethod
    async def update_progress(data, current_user):
        db = db_client.mongodb.get_default_database()
        await db["reading_history"].update_one(
            {"user_id": str(current_user.id), "document_id": data.document_id}, 
            {"$set": {
                "progress_percentage": min(100.0, max(0.0, data.progress_percentage)), 
                "current_chapter_slug": data.current_chapter_slug, 
                "last_read_at": datetime.utcnow()
            }}, 
            upsert=True
        )
        return {"status": "success"}

    @staticmethod
    async def get_continue_reading(current_user) -> list:
        db = db_client.mongodb.get_default_database()
        history = await db["reading_history"].find(
            {"user_id": str(current_user.id), "progress_percentage": {"$lt": 100, "$gt": 0}}
        ).sort("last_read_at", -1).limit(3).to_list(length=3)
        
        result = []
        for h in history:
            doc = await db["documents"].find_one({"_id": h["document_id"]}, {"title": 1, "slug": 1, "cover_url": 1})
            if doc:
                result.append({
                    "document_id": h["document_id"],
                    "document_title": doc.get("title", ""),
                    "document_slug": doc.get("slug", ""),
                    "cover_url": doc.get("cover_url"),
                    "progress_percentage": h.get("progress_percentage", 0),
                    "current_chapter_slug": h.get("current_chapter_slug"),
                    "last_read_at": h["last_read_at"].isoformat() if isinstance(h.get("last_read_at"), datetime) else "",
                })
        return result

    @staticmethod
    async def set_reading_goal(data, current_user) -> dict:
        db = db_client.mongodb.get_default_database()
        await db["reading_goals"].update_one(
            {"user_id": str(current_user.id)},
            {"$set": {
                "target_documents": max(0, data.target_documents),
                "target_pages": max(0, data.target_pages),
                "period": data.period if data.period in ["weekly", "monthly", "yearly"] else "monthly",
                "updated_at": datetime.utcnow(),
            }},
            upsert=True,
        )
        return {"message": "Đã thiết lập mục tiêu đọc tài liệu thành công."}

    @staticmethod
    async def get_reading_goal(current_user) -> dict:
        db = db_client.mongodb.get_default_database()
        goal = await db["reading_goals"].find_one({"user_id": str(current_user.id)})
        if not goal:
            return {"target_documents": 0, "target_pages": 0, "period": "monthly", "progress_documents": 0}
            
        history_count = await db["reading_history"].count_documents(
            {"user_id": str(current_user.id), "progress_percentage": 100}
        )
        return {
            "target_documents": goal.get("target_documents", 0),
            "target_pages": goal.get("target_pages", 0),
            "period": goal.get("period", "monthly"),
            "progress_documents": history_count,
        }

    @staticmethod
    async def search_in_document(document_id: str, query: str, current_user) -> dict:
        db = db_client.mongodb.get_default_database()
        doc = await db["documents"].find_one({"_id": document_id}, {"content": 1, "title": 1, "chapters": 1})
        if not doc:
            raise HTTPException(status_code=404, detail="Tài liệu không tồn tại.")
        content = doc.get("content", "")
        query_lower = query.lower()
        content_lower = content.lower()
        results = []
        search_from = 0
        while len(results) < 20:
            idx = content_lower.find(query_lower, search_from)
            if idx == -1:
                break
            start = max(0, idx - 60)
            end = min(len(content), idx + len(query) + 60)
            snippet = content[start:end]
            results.append({"offset": idx, "snippet": snippet})
            search_from = idx + len(query)
        return {"total": len(results), "results": results, "query": query}

    @staticmethod
    async def get_pinned_documents(current_user) -> list:
        db = db_client.mongodb.get_default_database()
        user = await db["users"].find_one({"_id": str(current_user.id)}, {"pinned_documents": 1})
        if not user or "pinned_documents" not in user:
            return []
            
        doc_ids = user["pinned_documents"]
        docs = await db["documents"].find({"_id": {"$in": doc_ids}}).to_list(length=len(doc_ids))
        
        doc_map = {str(d["_id"]): d for d in docs}
        result = []
        for d_id in doc_ids:
            if d_id in doc_map:
                d = doc_map[d_id]
                result.append({
                    "id": str(d["_id"]),
                    "title": d.get("title", ""),
                    "slug": d.get("slug", ""),
                    "cover_url": d.get("cover_url"),
                    "author_id": d.get("author_id")
                })
        return result

    @staticmethod
    async def pin_document(document_id: str, current_user) -> dict:
        db = db_client.mongodb.get_default_database()
        await db["users"].update_one(
            {"_id": str(current_user.id)},
            {"$addToSet": {"pinned_documents": document_id}}
        )
        return {"status": "success"}

    @staticmethod
    async def unpin_document(document_id: str, current_user) -> dict:
        db = db_client.mongodb.get_default_database()
        await db["users"].update_one(
            {"_id": str(current_user.id)},
            {"$pull": {"pinned_documents": document_id}}
        )
        return {"status": "success"}

    @staticmethod
    async def set_pinned_documents(document_ids: list, current_user) -> dict:
        db = db_client.mongodb.get_default_database()
        await db["users"].update_one(
            {"_id": str(current_user.id)},
            {"$set": {"pinned_documents": document_ids}}
        )
        return {"status": "success"}
