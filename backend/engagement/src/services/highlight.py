import uuid
from datetime import datetime, timezone
from fastapi import HTTPException
from loguru import logger
from src.core.logic_logger import log_logic_execution
from src.repositories.highlight import HighlightRepository
from src.repositories.reading import DocumentRepository

ALLOWED_HIGHLIGHT_COLORS = ["#18181b", "#71717a", "#e4e4e7"]

class HighlightService:

    @staticmethod
    @log_logic_execution
    async def create_highlight(
        document_id: str, data: dict, current_user
    ) -> dict:
        color = data.get("color", "#e4e4e7")
        if color not in ALLOWED_HIGHLIGHT_COLORS:
            color = "#e4e4e7"
        highlight = {
            "_id": str(uuid.uuid4()),
            "user_id": str(current_user.id),
            "document_id": document_id,
            "text": data["text"],
            "color": color,
            "start_offset": data.get("start_offset", 0),
            "end_offset": data.get("end_offset", 0),
            "note": data.get("note", ""),
            "created_at": datetime.now(timezone.utc),
        }
        await HighlightRepository.insert_one(highlight)
        logger.info("Document text highlight created")
        return highlight

    @staticmethod
    @log_logic_execution
    async def get_highlights(document_id: str, current_user) -> list:
        highlights = (
            await HighlightRepository
            .find({"user_id": str(current_user.id), "document_id": document_id})
            .sort("created_at", -1)
            .to_list(length=None)
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
    @log_logic_execution
    async def update_highlight_note(
        highlight_id: str, note: str, current_user
    ) -> dict:
        result = await HighlightRepository.update_one(
            {"_id": highlight_id, "user_id": str(current_user.id)},
            {"$set": {"note": note, "updated_at": datetime.now(timezone.utc)}},
        )
        if result.matched_count == 0:
            raise HTTPException(
                status_code=404, detail="Hệ thống không tìm thấy dữ liệu đánh dấu văn bản yêu cầu"
            )
        return {"message": "Cập nhật nội dung ghi chú cho đoạn văn bản nổi bật hoàn tất"}

    @staticmethod
    @log_logic_execution
    async def delete_highlight(highlight_id: str, current_user) -> dict:
        result = await HighlightRepository.delete_one(
            {"_id": highlight_id, "user_id": str(current_user.id)}
        )
        if result.deleted_count == 0:
            raise HTTPException(
                status_code=404, detail="Hệ thống không tìm thấy dữ liệu đánh dấu văn bản yêu cầu"
            )
        logger.info("Document highlight and associated note permanently deleted")
        return {"message": "Dữ liệu đánh dấu văn bản đã được xóa vĩnh viễn khỏi hệ thống"}

    @staticmethod
    @log_logic_execution
    async def get_all_notes(
        current_user,
        cursor: str = None,
        limit: int = 50,
        skip: int = 0,
    ) -> list:
        match_query = {"user_id": str(current_user.id), "note": {"$ne": ""}}
        if cursor:
            try:
                match_query["created_at"] = {
                    "$lt": datetime.fromisoformat(cursor.replace("Z", "+00:00"))
                }
            except ValueError:
                logger.warning("Rejected malformed pagination cursor")
                raise HTTPException(status_code=400, detail="Con trỏ phân trang không hợp lệ")
        pipeline = [{"$match": match_query}, {"$sort": {"created_at": -1}}]
        if skip > 0:
            pipeline.append({"$skip": skip})
        pipeline.append({"$limit": limit})
        pipeline.extend(
            [
                {
                    "$lookup": {
                        "from": "documents",
                        "localField": "document_id",
                        "foreignField": "_id",
                        "as": "doc",
                    }
                },
                {"$unwind": {"path": "$doc", "preserveNullAndEmptyArrays": True}},
            ]
        )
        highlights = (
            await HighlightRepository
            .aggregate(pipeline)
            .to_list(length=None)
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
    @log_logic_execution
    async def export_highlights_markdown(
        document_id: str, current_user
    ) -> dict:
        document = await DocumentRepository.find_one(
            {"_id": document_id}, projection={"title": 1}
        )
        document_title = document.get("title", "Untitled") if document else "Untitled"
        highlights = (
            await HighlightRepository
            .find({"user_id": str(current_user.id), "document_id": document_id})
            .sort("created_at", 1)
            .to_list(length=None)
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
