from fastapi import HTTPException
from src.core.logic_logger import log_logic_execution
from src.repositories.cloud import CloudRepository

class PreviewService:

    @staticmethod
    @log_logic_execution
    async def get_preview_payload(item_id: str, owner_id: str) -> dict:
        item = await CloudRepository.find_one({"_id": item_id, "owner_id": owner_id})
        if not item:
            raise HTTPException(status_code=404, detail="Không tìm thấy tệp tin")
        mime = item.get("mime_type", "").lower()
        name = item.get("name", "").lower()
        preview_type = "generic"
        if "pdf" in mime or name.endswith(".pdf"):
            preview_type = "pdf"
        elif "image" in mime or name.endswith((".png", ".jpg", ".jpeg", ".webp")):
            preview_type = "image"
        elif "video" in mime or name.endswith((".mp4", ".webm")):
            preview_type = "video"
        elif "text" in mime or name.endswith((".txt", ".py", ".js", ".json", ".md")):
            preview_type = "text"
        can_preview = bool(item.get("url")) and preview_type != "generic"
        stream_url = None
        if can_preview:
            preview = await CloudRepository.preview_url(item_id, owner_id)
            stream_url = preview.get("preview_url") if preview else None
        return {
            "item_id": item_id,
            "name": item.get("name"),
            "size": item.get("size"),
            "preview_type": preview_type,
            "stream_url": stream_url,
            "can_preview": can_preview
        }
