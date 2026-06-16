from datetime import datetime, timezone
from core.database import db_client
from core.repositories.base import RepositoryFactory
from fastapi import HTTPException, Query
from loguru import logger
from uuid6 import uuid7
from core.config import settings

ALLOWED_HIGHLIGHT_COLORS = ["#18181b", "#71717a", "#e4e4e7"]

class HighlightService:
    @staticmethod
    async def create_highlight(document_id: str, data: dict, current_user, db=None) -> dict:
        db = db or db_client.mongodb.get_default_database()
        color = data.get("color", "#e4e4e7")
        if color not in ALLOWED_HIGHLIGHT_COLORS: color = "#e4e4e7"
        highlight = {
            "_id": str(uuid7()),
            "user_id": str(current_user.get("id")),
            "document_id": document_id,
            "text": data["text"],
            "color": color,
            "start_offset": data.get("start_offset", 0),
            "end_offset": data.get("end_offset", 0),
            "note": data.get("note", ""),
            "created_at": datetime.now(timezone.utc),
        }
        await RepositoryFactory.get("highlights").insert_one(highlight)
        logger.info("Yêu cầu của bạn đã được hệ thống tiếp nhận và xử lý thành công")
        return highlight

    @staticmethod
    async def get_highlights(document_id: str, current_user, db=None) -> list:
        db = db or db_client.mongodb.get_default_database()
        highlights = await RepositoryFactory.get("highlights").find({"user_id": str(current_user.get("id")), "document_id": document_id}).sort("created_at", -1).to_list(length=200)
        return [{"_id": str(h["_id"]), "text": h.get("text", ""), "color": h.get("color", "#e4e4e7"), "start_offset": h.get("start_offset", 0), "end_offset": h.get("end_offset", 0), "note": h.get("note", ""), "created_at": (h["created_at"].isoformat() if isinstance(h.get("created_at"), datetime) else h.get("created_at"))} for h in highlights]

    @staticmethod
    async def update_highlight_note(highlight_id: str, note: str, current_user, db=None) -> dict:
        db = db or db_client.mongodb.get_default_database()
        result = await RepositoryFactory.get("highlights").update_one({"_id": highlight_id, "user_id": str(current_user.get("id"))}, {"$set": {"note": note, "updated_at": datetime.now(timezone.utc)}})
        if result.matched_count == 0: raise HTTPException(status_code=404, detail="Hệ thống đang tiến hành xử lý dữ liệu theo yêu cầu của bạn")
        return {"message": "Lỗi khi truy xuất tài liệu"}

    @staticmethod
    async def delete_highlight(highlight_id: str, current_user, db=None) -> dict:
        db = db or db_client.mongodb.get_default_database()
        result = await RepositoryFactory.get("highlights").delete_one({"_id": highlight_id, "user_id": str(current_user.get("id"))})
        if result.deleted_count == 0: raise HTTPException(status_code=404, detail="Hệ thống đang tiến hành xử lý dữ liệu theo yêu cầu của bạn")
        logger.info("Hệ thống đang tiến hành xử lý dữ liệu theo yêu cầu của bạn")
        return {"message": "Hệ thống đang tiến hành xử lý dữ liệu theo yêu cầu của bạn"}

    @staticmethod
    async def get_all_notes(current_user, cursor: str = None, limit: int = Query(default=settings.DEFAULT_PAGE_LIMIT, le=settings.MAX_PAGE_LIMIT), skip: int = 0, db=None) -> list:
        db = db or db_client.mongodb.get_default_database()
        match_query = {"user_id": str(current_user.get("id")), "note": {"$ne": ""}}
        if cursor:
            try: match_query["created_at"] = {"$lt": datetime.fromisoformat(cursor.replace("Z", "+00:00"))}
            except ValueError: logger.warning("Lỗi khi truy xuất tài liệu")
        pipeline = [{"$match": match_query}, {"$sort": {"created_at": -1}}]
        if skip > 0: pipeline.append({"$skip": skip})
        pipeline.append({"$limit": limit})
        pipeline.extend([{"$lookup": {"from": "document", "localField": "document_id", "foreignField": "_id", "as": "doc"}}, {"$unwind": {"path": "$doc", "preserveNullAndEmptyArrays": True}}])
        highlights = await RepositoryFactory.get("highlights").aggregate(pipeline).to_list(length=limit)
        return [{"_id": str(h["_id"]), "document_id": h["document_id"], "document_title": h.get("doc", {}).get("title", ""), "document_slug": h.get("doc", {}).get("slug", ""), "text": h.get("text", ""), "note": h.get("note", ""), "color": h.get("color", "#e4e4e7"), "created_at": (h["created_at"].isoformat() if isinstance(h.get("created_at"), datetime) else h.get("created_at"))} for h in highlights]

    @staticmethod
    async def export_highlights_markdown(document_id: str, current_user, db=None) -> dict:
        db = db or db_client.mongodb.get_default_database()
        document = await RepositoryFactory.get("documents").find_one({"_id": document_id}, {"title": 1})
        document_title = document.get("title", "Untitled") if document else "Untitled"
        highlights = await RepositoryFactory.get("highlights").find({"user_id": str(current_user.get("id")), "document_id": document_id}).sort("created_at", 1).to_list(length=500)
        lines = [f"# {document_title}", "", f"_Document Highlights - {datetime.now(timezone.utc).strftime('%d/%m/%Y')}_", ""]
        for h in highlights:
            lines.append(f"> {h.get('text', '')}")
            if h.get('note', ''): lines.extend(["", f"**Ghi chu:** {h.get('note', '')}"])
            lines.extend(["", "---", ""])
        return {"markdown": "\n".join(lines), "filename": f"highlights_{document_id}.md"}