import uuid
from datetime import datetime, timezone

from fastapi import HTTPException, Query
from loguru import logger
from uuid6 import uuid7

from shared.infrastructure.configuration import settings
from shared.infrastructure.database import database
from shared.repositories.database import BaseRepository

ALLOWED_HIGHLIGHT_COLORS = ["#18181b", "#71717a", "#e4e4e7"]


class HighlightService:

    @staticmethod
    async def create_highlight(
        document_id: str, data: dict, current_user, db=None
    ) -> dict:
        if db is None:
            db = database.mongodb.get_default_database()
        color = data.get("color", "#e4e4e7")
        if color not in ALLOWED_HIGHLIGHT_COLORS:
            color = "#e4e4e7"
        highlight = {
            "_id": str(uuid7()),
            "user_id": str(current_user.id),
            "document_id": document_id,
            "text": data["text"],
            "color": color,
            "start_offset": data.get("start_offset", 0),
            "end_offset": data.get("end_offset", 0),
            "note": data.get("note", ""),
            "created_at": datetime.now(timezone.utc),
        }
        await BaseRepository.get("highlights").insert_one(highlight)
        logger.info("Tạo phần văn bản nổi bật thành công")
        return highlight

    @staticmethod
    async def get_highlights(document_id: str, current_user, db=None) -> list:
        if db is None:
            db = database.mongodb.get_default_database()
        highlights = (
            await BaseRepository.get("highlights")
            .find({"user_id": str(current_user.id), "document_id": document_id})
            .sort("created_at", -1)
            .to_list(length=200)
        )
        return [
            {
                "_id": str(h["_id"]),
                "text": h.get("text", ""),
                "color": h.get("color", "#e4e4e7"),
                "start_offset": h.get("start_offset", 0),
                "end_offset": h.get("end_offset", 0),
                "note": h.get("note", ""),
                "created_at": (
                    h["created_at"].isoformat()
                    if isinstance(h.get("created_at"), datetime)
                    else h.get("created_at")
                ),
            }
            for h in highlights
        ]

    @staticmethod
    async def update_highlight_note(
        highlight_id: str, note: str, current_user, db=None
    ) -> dict:
        if db is None:
            db = database.mongodb.get_default_database()
        result = await BaseRepository.get("highlights").update_one(
            {"_id": highlight_id, "user_id": str(current_user.id)},
            {"$set": {"note": note, "updated_at": datetime.now(timezone.utc)}},
        )
        if result.matched_count == 0:
            raise HTTPException(
                status_code=404, detail="Không tìm thấy ghi chú đánh dấu"
            )
        return {"message": "Cập nhật chú thích đoạn nổi bật thành công"}

    @staticmethod
    async def delete_highlight(highlight_id: str, current_user, db=None) -> dict:
        if db is None:
            db = database.mongodb.get_default_database()
        result = await BaseRepository.get("highlights").delete_one(
            {"_id": highlight_id, "user_id": str(current_user.id)}
        )
        if result.deleted_count == 0:
            raise HTTPException(
                status_code=404, detail="Không tìm thấy ghi chú đánh dấu"
            )
        logger.info("Xóa vĩnh viễn ghi chú và phần đánh dấu")
        return {"message": "Đã xóa phần đánh dấu văn bản"}

    @staticmethod
    async def get_all_notes(
        current_user,
        cursor: str = None,
        limit: int = 50,
        skip: int = 0,
        db=None,
    ) -> list:
        if db is None:
            db = database.mongodb.get_default_database()
        match_query = {"user_id": str(current_user.id), "note": {"$ne": ""}}
        if cursor:
            try:
                match_query["created_at"] = {
                    "$lt": datetime.fromisoformat(cursor.replace("Z", "+00:00"))
                }
            except ValueError as e:
                logger.warning(f"Lỗi định dạng phân trang: {e}")
        pipeline = [{"$match": match_query}, {"$sort": {"created_at": -1}}]
        if skip > 0:
            pipeline.append({"$skip": skip})
        pipeline.append({"$limit": limit})
        pipeline.extend(
            [
                {
                    "$lookup": {
                        "from": "document",
                        "localField": "document_id",
                        "foreignField": "_id",
                        "as": "doc",
                    }
                },
                {"$unwind": {"path": "$doc", "preserveNullAndEmptyArrays": True}},
            ]
        )
        highlights = (
            await BaseRepository.get("highlights")
            .aggregate(pipeline)
            .to_list(length=limit)
        )
        result = []
        for h in highlights:
            document = h.get("doc", {})
            result.append(
                {
                    "_id": str(h["_id"]),
                    "document_id": h["document_id"],
                    "document_title": document.get("title", "") if document else "",
                    "document_slug": document.get("slug", "") if document else "",
                    "text": h.get("text", ""),
                    "note": h.get("note", ""),
                    "color": h.get("color", "#e4e4e7"),
                    "created_at": (
                        h["created_at"].isoformat()
                        if isinstance(h.get("created_at"), datetime)
                        else h.get("created_at")
                    ),
                }
            )
        return result

    @staticmethod
    async def export_highlights_markdown(
        document_id: str, current_user, db=None
    ) -> dict:
        if db is None:
            db = database.mongodb.get_default_database()
        document = await BaseRepository.get("documents").find_one(
            {"_id": document_id}, projection={"title": 1}
        )
        document_title = document.get("title", "Untitled") if document else "Untitled"
        highlights = (
            await BaseRepository.get("highlights")
            .find({"user_id": str(current_user.id), "document_id": document_id})
            .sort("created_at", 1)
            .to_list(length=500)
        )
        lines = [
            f"# {document_title}",
            "",
            f"_Document Highlights - {datetime.now(timezone.utc).strftime('%d/%m/%Y')}_",
            "",
        ]
        for h in highlights:
            text = h.get("text", "")
            note = h.get("note", "")
            lines.append(f"> {text}")
            if note:
                lines.append("")
                lines.append(f"**Ghi chu:** {note}")
            lines.append("")
            lines.append("---")
            lines.append("")
        return {
            "markdown": "\n".join(lines),
            "filename": f"highlights_{document_id}.md",
        }
