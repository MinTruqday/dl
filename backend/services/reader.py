from core.config import settings
from core.database import db_client
from fastapi import HTTPException
from datetime import datetime, timedelta
import uuid
import json
import os
import httpx
from loguru import logger

class ReaderService:
    @staticmethod
    async def update_typography(data: dict, current_user) -> dict:
        db = db_client.mongodb.get_default_database()
        allowed_fonts = ["Inter", "Roboto", "Outfit", "Noto Sans", "Source Sans Pro"]
        font = data.get("font_family", "Inter")
        if font not in allowed_fonts: raise HTTPException(status_code=400, detail="Font chữ không được hỗ trợ.")
        update_data = {"font_family": font, "font_size": max(12, min(28, data.get("font_size", 16))), "line_height": max(1.2, min(3.0, data.get("line_height", 1.8))), "letter_spacing": max(-0.5, min(2.0, data.get("letter_spacing", 0))), "updated_at": datetime.utcnow()}
        await db["reading_preferences"].update_one({"user_id": str(current_user.id)}, {"$set": update_data}, upsert=True)
        return {"message": "Đã cập nhật tùy chỉnh kiểu chữ."}

    @staticmethod
    async def get_privacy_settings(current_user) -> dict:
        db = db_client.mongodb.get_default_database()
        user = await db["users"].find_one({"_id": str(current_user.id)})
        return {"hide_reading_activity": user.get("privacy_hide_reading", False) if user else False, "hide_library": user.get("privacy_hide_library", False) if user else False}

    @staticmethod
    async def update_privacy_settings(data: dict, current_user) -> dict:
        db = db_client.mongodb.get_default_database()
        await db["users"].update_one({"_id": str(current_user.id)}, {"$set": {"privacy_hide_reading": data.get("hide_reading_activity", False), "privacy_hide_library": data.get("hide_library", False), "updated_at": datetime.utcnow()}})
        return {"message": "Đã cập nhật cài đặt riêng tư."}

    @staticmethod
    async def get_reading_history(current_user, skip: int = 0, limit: int = 20) -> list:
        db = db_client.mongodb.get_default_database()
        history = await db["reading_history"].find({"user_id": str(current_user.id)}).sort("last_read_at", -1).skip(skip).limit(limit).to_list(length=limit)
        result = []
        for h in history:
            doc = await db["documents"].find_one({"_id": h["document_id"]}, {"title": 1, "slug": 1, "cover_url": 1})
            if doc:
                result.append({"document_id": h["document_id"], "document_title": doc.get("title", ""), "document_slug": doc.get("slug", ""), "cover_url": doc.get("cover_url"), "progress_percentage": h.get("progress_percentage", 0), "last_read_at": h["last_read_at"].isoformat() if isinstance(h.get("last_read_at"), datetime) else ""})
        return result

    @staticmethod
    async def update_progress(data, current_user):
        db = db_client.mongodb.get_default_database()
        await db["reading_history"].update_one({"user_id": str(current_user.id), "document_id": data.document_id}, {"$set": {"progress_percentage": min(100.0, max(0.0, data.progress_percentage)), "current_chapter_slug": data.current_chapter_slug, "last_read_at": datetime.utcnow()}}, upsert=True)
        return {"status": "success"}

    @staticmethod
    async def add_document_to_list(list_id: str, document_id: str, current_user) -> dict:
        db = db_client.mongodb.get_default_database()
        result = await db["reading_lists"].update_one(
            {"_id": list_id, "user_id": str(current_user.id)},
            {"$addToSet": {"documents": document_id}, "$set": {"updated_at": datetime.utcnow()}}
        )
        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="Không tìm thấy danh sách đọc.")
        return {"status": "success", "message": "Đã thêm vào danh sách."}

    @staticmethod
    async def remove_document_from_list(list_id: str, document_id: str, current_user) -> dict:
        db = db_client.mongodb.get_default_database()
        result = await db["reading_lists"].update_one(
            {"_id": list_id, "user_id": str(current_user.id)},
            {"$pull": {"documents": document_id}, "$set": {"updated_at": datetime.utcnow()}}
        )
        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="Không tìm thấy danh sách đọc.")
        return {"status": "success", "message": "Đã xóa khỏi danh sách."}

    @staticmethod
    async def get_reading_stats(current_user) -> dict:
        db = db_client.mongodb.get_default_database()
        history = await db["reading_history"].find({"user_id": str(current_user.id)}).to_list(length=500)
        total_time = sum(h.get("time_spent_seconds", 0) for h in history)
        return {"total_documents_read": len(history), "total_time_minutes": round(total_time / 60, 1), "average_progress": round(sum(h.get("progress_percentage", 0) for h in history) / max(len(history), 1), 1)}

    @staticmethod
    async def get_reading_stats_chart(current_user) -> dict:
        db = db_client.mongodb.get_default_database()
        pipeline = [
            {"$match": {"user_id": str(current_user.id)}},
            {"$group": {
                "_id": {
                    "year": {"$year": "$last_read_at"},
                    "month": {"$month": "$last_read_at"},
                },
                "documents_read": {"$sum": 1},
                "total_time_seconds": {"$sum": "$time_spent_seconds"},
                "avg_progress": {"$avg": "$progress_percentage"},
            }},
            {"$sort": {"_id.year": 1, "_id.month": 1}},
            {"$limit": 12},
        ]
        results = await db["reading_history"].aggregate(pipeline).to_list(length=12)
        chart_data = []
        for r in results:
            chart_data.append({
                "month": f"{r['_id']['year']}-{str(r['_id']['month']).zfill(2)}",
                "documents_read": r.get("documents_read", 0),
                "total_time_minutes": round(r.get("total_time_seconds", 0) / 60, 1),
                "avg_progress": round(r.get("avg_progress", 0), 1),
            })
        return {"chart_data": chart_data}

    @staticmethod
    async def create_reading_list(data, current_user):
        db = db_client.mongodb.get_default_database()
        new_list = {"_id": str(uuid.uuid4()), "user_id": str(current_user.id), "name": data.name, "description": data.description, "is_public": data.is_public, "documents": [], "created_at": datetime.utcnow()}
        await db["reading_lists"].insert_one(new_list)
        return new_list

    @staticmethod
    async def get_my_reading_lists(current_user):
        db = db_client.mongodb.get_default_database()
        return await db["reading_lists"].find({"user_id": str(current_user.id)}).to_list(100)

    @staticmethod
    async def share_excerpt(data: dict, current_user) -> dict:
        db = db_client.mongodb.get_default_database()
        doc = await db["documents"].find_one({"_id": data["document_id"]})
        if not doc: raise HTTPException(status_code=404, detail="Tài liệu không tồn tại.")
        excerpt_post = {"_id": str(uuid.uuid4()), "user_id": str(current_user.id), "content": data.get("caption", ""), "item_type": "excerpt", "excerpt_text": data["text"], "attached_document_id": data["document_id"], "attached_document_title": doc.get("title", ""), "privacy": "public", "created_at": datetime.utcnow()}
        await db["status_updates"].insert_one(excerpt_post)
        return {"message": "Đã chia sẻ trích đoạn.", "post_id": excerpt_post["_id"]}

    @staticmethod
    async def rate_document(document_id, rating_data, current_user):
        db = db_client.mongodb.get_default_database()
        await db["reviews"].update_one({"user_id": str(current_user.id), "document_id": document_id}, {"$set": {"rating": rating_data.rating, "review_text": rating_data.review_text, "created_at": datetime.utcnow()}}, upsert=True)
        return {"status": "success"}

    @staticmethod
    async def semantic_search(query: str, current_user) -> list:
        rag_url = getattr(settings, "AGENTIC_RAG_URL", None)
        if not rag_url: raise HTTPException(status_code=500, detail="Dịch vụ AI chưa được cấu hình.")
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                resp = await client.post(f"{rag_url}/chat", json={
                    "query": f"Tìm kiếm tài liệu liên quan đến: {query}",
                    "user_id": str(current_user.id),
                    "useSmart": True
                })
                if resp.status_code == 200:
                    data = resp.json()
                    return data
        except Exception as e:
            logger.error(f"Semantic Search Proxy Error: {e}")
            raise HTTPException(status_code=500, detail="Lỗi kết nối đến dịch vụ AI.")

    @staticmethod
    async def generate_flashcard(document_id: str, payload, current_user):
        rag_url = getattr(settings, "AGENTIC_RAG_URL", None)
        if not rag_url: raise HTTPException(status_code=500, detail="Dịch vụ AI hiện chưa được cấu hình.")
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                resp = await client.post(f"{rag_url}/api/inference/generate-flashcard", json={"text": payload.text, "context": payload.context})
                if resp.status_code == 200:
                    data = resp.json()
                    db = db_client.mongodb.get_default_database()
                    flashcard = {"_id": str(uuid.uuid4()), "user_id": str(current_user.id), "document_id": document_id, "front": data.get("front"), "back": data.get("back"), "created_at": datetime.utcnow()}
                    await db["flashcards"].insert_one(flashcard)
                    return data
        except Exception as e:
            logger.error(f"Flashcard Proxy Error: {e}")
            raise HTTPException(status_code=500, detail="Không thể kết nối đến dịch vụ AI lúc này.")
            
    @staticmethod
    async def review_flashcard(payload, current_user):
        import math
        db = db_client.mongodb.get_default_database()
        card_id = payload.get("card_id")
        quality = payload.get("quality", 3)
        try:
            from bson import ObjectId
            oid = ObjectId(card_id)
        except:
            raise HTTPException(status_code=400, detail="ID không hợp lệ.")
            
        card = await db["flashcards"].find_one({"_id": oid, "user_id": str(current_user.id)})
        if not card:
            raise HTTPException(status_code=404, detail="Không tìm thấy flashcard.")
            
        rep = card.get("repetitions", 0)
        ef = card.get("easiness_factor", 2.5)
        interval = card.get("interval", 1)
        
        if quality >= 3:
            if rep == 0: interval = 1
            elif rep == 1: interval = 6
            else: interval = math.ceil(interval * ef)
            rep += 1
        else:
            rep = 0
            interval = 1
            
        ef = max(1.3, ef + (0.1 - (5 - quality) * (0.08 + (5 - quality) * 0.02)))
        next_review = datetime.utcnow() + timedelta(days=interval)
        
        await db["flashcards"].update_one(
            {"_id": oid},
            {"$set": {"repetitions": rep, "easiness_factor": ef, "interval": interval, "next_review": next_review}}
        )
        return {"message": "Đã xếp lịch lặp lại ngắt quãng", "next_review": next_review.isoformat()}

    @staticmethod
    async def get_document_reviews(document_id: str) -> list:
        db = db_client.mongodb.get_default_database()
        reviews = await db["reviews"].find({"document_id": document_id}).sort("created_at", -1).to_list(length=100)
        for r in reviews:
            r["_id"] = str(r["_id"])
        return reviews

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
    async def create_bookmark_folder(name: str, current_user) -> dict:
        db = db_client.mongodb.get_default_database()
        folder = {
            "_id": str(uuid.uuid4()),
            "user_id": str(current_user.id),
            "name": name.strip()[:100],
            "bookmark_ids": [],
            "created_at": datetime.utcnow(),
        }
        await db["bookmark_folders"].insert_one(folder)
        logger.info(f"Bookmark folder created by user {current_user.id}: {folder['_id']}")
        return folder

    @staticmethod
    async def get_bookmark_folders(current_user) -> list:
        db = db_client.mongodb.get_default_database()
        folders = await db["bookmark_folders"].find(
            {"user_id": str(current_user.id)}
        ).sort("created_at", -1).to_list(length=50)
        return [{
            "id": str(f["_id"]),
            "name": f.get("name", ""),
            "bookmark_ids": f.get("bookmark_ids", []),
            "created_at": f["created_at"].isoformat() if isinstance(f.get("created_at"), datetime) else "",
        } for f in folders]

    @staticmethod
    async def assign_bookmarks_to_folder(folder_id: str, bookmark_ids: list, current_user) -> dict:
        db = db_client.mongodb.get_default_database()
        result = await db["bookmark_folders"].update_one(
            {"_id": folder_id, "user_id": str(current_user.id)},
            {"$set": {"bookmark_ids": bookmark_ids, "updated_at": datetime.utcnow()}}
        )
        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="Thư mục không tồn tại.")
        return {"message": "Đã cập nhật thư mục đánh dấu thành công."}

    @staticmethod
    async def delete_bookmark_folder(folder_id: str, current_user) -> dict:
        db = db_client.mongodb.get_default_database()
        result = await db["bookmark_folders"].delete_one({"_id": folder_id, "user_id": str(current_user.id)})
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Thư mục không tồn tại.")
        return {"message": "Đã xóa thư mục đánh dấu thành công."}

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
        logger.info(f"Chapter {data.chapter_slug} rated {data.rating} by user {current_user.id}")
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
        logger.info(f"Typo report submitted by user {current_user.id} for document {document_id}")
        return {"message": "Đã gửi báo cáo lỗi chính tả thành công. Cảm ơn đóng góp của bạn."}

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
    async def set_pinned_documents(document_ids: list, current_user) -> dict:
        db = db_client.mongodb.get_default_database()
        if len(document_ids) > 3:
            raise HTTPException(status_code=400, detail="Chỉ được ghim tối đa 3 tài liệu.")
        await db["users"].update_one(
            {"_id": str(current_user.id)},
            {"$set": {"pinned_documents": document_ids[:3], "updated_at": datetime.utcnow()}}
        )
        return {"message": "Đã cập nhật danh sách ghim thành công."}

    @staticmethod
    async def get_pinned_documents(current_user) -> list:
        db = db_client.mongodb.get_default_database()
        user = await db["users"].find_one({"_id": str(current_user.id)}, {"pinned_documents": 1})
        pinned_ids = user.get("pinned_documents", []) if user else []
        if not pinned_ids:
            return []
        docs = await db["documents"].find(
            {"_id": {"$in": pinned_ids}}
        ).to_list(length=3)
        return [{
            "id": str(d["_id"]),
            "title": d.get("title", ""),
            "slug": d.get("slug", ""),
            "cover_url": d.get("cover_url"),
        } for d in docs]

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
