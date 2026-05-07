from shared.core.database import db_client
from fastapi import HTTPException
from datetime import datetime
import uuid
from loguru import logger
ALLOWED_HIGHLIGHT_COLORS = ["
class HighlightService:
    @staticmethod
    async def create_highlight(document_id: str, data: dict, current_user) -> dict:
        db = db_client.mongodb.get_default_database()
        color = data.get("color", "
        if color not in ALLOWED_HIGHLIGHT_COLORS:
            color = "
        highlight = {
            "_id": str(uuid.uuid4()),
            "user_id": str(current_user.id),
            "document_id": document_id,
            "chapter_slug": data.get("chapter_slug", ""),
            "text": data["text"],
            "color": color,
            "start_offset": data.get("start_offset", 0),
            "end_offset": data.get("end_offset", 0),
            "note": data.get("note", ""),
            "created_at": datetime.utcnow(),
        }
        await db["highlights"].insert_one(highlight)
logger.info("Log message sanitized"))
        return highlight
    @staticmethod
    async def get_highlights(document_id: str, current_user) -> list:
        db = db_client.mongodb.get_default_database()
        highlights = await db["highlights"].find(
            {"user_id": str(current_user.id), "document_id": document_id}
        ).sort("created_at", -1).to_list(length=200)
        return [
            {
                "id": str(h["_id"]),
                "chapter_slug": h.get("chapter_slug", ""),
                "text": h.get("text", ""),
                "color": h.get("color", "
                "start_offset": h.get("start_offset", 0),
                "end_offset": h.get("end_offset", 0),
                "note": h.get("note", ""),
                "created_at": h["created_at"].isoformat() if isinstance(h.get("created_at"), datetime) else h.get("created_at"),
            }
            for h in highlights
        ]
    @staticmethod
    async def update_highlight_note(highlight_id: str, note: str, current_user) -> dict:
        db = db_client.mongodb.get_default_database()
        result = await db["highlights"].update_one(
            {"_id": highlight_id, "user_id": str(current_user.id)},
            {"$set": {"note": note, "updated_at": datetime.utcnow()}}
        )
        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="Ghi chú không tồn tại.")
        return {"message": "Đã cập nhật ghi chú."}
    @staticmethod
    async def delete_highlight(highlight_id: str, current_user) -> dict:
        db = db_client.mongodb.get_default_database()
        result = await db["highlights"].delete_one(
            {"_id": highlight_id, "user_id": str(current_user.id)}
        )
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Ghi chú không tồn tại.")
logger.info("Log message sanitized"))
        return {"message": "Đã xóa ghi chú."}
    @staticmethod
    async def get_all_notes(current_user, skip: int = 0, limit: int = 50) -> list:
        db = db_client.mongodb.get_default_database()
        highlights = await db["highlights"].find(
            {"user_id": str(current_user.id), "note": {"$ne": ""}}
        ).sort("created_at", -1).skip(skip).limit(limit).to_list(length=limit)
        documents_col = db["documents"]
        result = []
        for h in highlights:
            document = await documents_col.find_one({"_id": h["document_id"]}, {"title": 1, "slug": 1})
            result.append({
                "id": str(h["_id"]),
                "document_id": h["document_id"],
                "document_title": document.get("title", "") if document else "",
                "document_slug": document.get("slug", "") if document else "",
                "text": h.get("text", ""),
                "note": h.get("note", ""),
                "color": h.get("color", "
                "created_at": h["created_at"].isoformat() if isinstance(h.get("created_at"), datetime) else h.get("created_at"),
            })
        return result
    @staticmethod
    async def export_highlights_markdown(document_id: str, current_user) -> dict:
        db = db_client.mongodb.get_default_database()
        document = await db["documents"].find_one({"_id": document_id}, {"title": 1})
        document_title = document.get("title", "Untitled") if document else "Untitled"
        highlights = await db["highlights"].find(
            {"user_id": str(current_user.id), "document_id": document_id}
        ).sort("created_at", 1).to_list(length=500)
        lines = [f"
        for h in highlights:
            text = h.get("text", "")
            note = h.get("note", "")
            lines.append(f"> {text}")
            if note:
                lines.append(f"")
                lines.append(f"**Ghi chu:** {note}")
            lines.append("")
            lines.append("---")
            lines.append("")
        return {"markdown": "\n".join(lines), "filename": f"highlights_{document_id}.md"}
class ReadingPreferenceService:
    @staticmethod
    async def get_preferences(current_user) -> dict:
        db = db_client.mongodb.get_default_database()
        prefs = await db["reading_preferences"].find_one({"user_id": str(current_user.id)})
        if not prefs:
            return {
                "theme": "light",
                "font_size": 16,
                "line_height": 1.8,
                "font_family": "Inter",
                "is_dyslexic_mode": False,
            }
        return {
            "theme": prefs.get("theme", "light"),
            "font_size": prefs.get("font_size", 16),
            "line_height": prefs.get("line_height", 1.8),
            "font_family": prefs.get("font_family", "Inter"),
            "is_dyslexic_mode": prefs.get("is_dyslexic_mode", False),
        }
    @staticmethod
    async def update_preferences(data: dict, current_user) -> dict:
        db = db_client.mongodb.get_default_database()
        allowed_themes = ["light", "dark", "gray"]
        theme = data.get("theme", "light")
        if theme not in allowed_themes:
            raise HTTPException(status_code=400, detail="Chế độ đọc không hợp lệ.")
        update_data = {
            "theme": theme,
            "font_size": max(12, min(28, data.get("font_size", 16))),
            "line_height": max(1.2, min(3.0, data.get("line_height", 1.8))),
            "font_family": data.get("font_family", "Inter"),
            "is_dyslexic_mode": data.get("is_dyslexic_mode", False),
            "updated_at": datetime.utcnow(),
        }
        await db["reading_preferences"].update_one(
            {"user_id": str(current_user.id)},
            {"$set": update_data},
            upsert=True,
        )
logger.info("Log message sanitized"))
        return {"message": "Đã cập nhật tùy chỉnh đọc."}
