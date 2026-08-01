from src.core.infrastructure.configuration import settings
from src.core.infrastructure.database import database
from src.core.logic_logger import log_logic_execution
from backend.cloud.src.services.user import UserDirectory

class AnalyticsService:
    @staticmethod
    @log_logic_execution
    async def analyze_storage_quota(owner_id: str) -> dict:
        cursor = database.mongodb[settings.CLOUD_DB_NAME].storage_items.find({"owner_id": owner_id, "is_trashed": False, "is_folder": False})
        items = await cursor.to_list(length=10000)
        breakdown = {"images": 0, "videos": 0, "documents": 0, "audio": 0, "archives": 0, "others": 0}
        total_used = 0
        for item in items:
            size = item.get("size", 0)
            mime = item.get("mime_type", "").lower()
            name = item.get("name", "").lower()
            total_used += size
            if "image" in mime or name.endswith((".png", ".jpg", ".jpeg", ".webp", ".gif")):
                breakdown["images"] += size
            elif "video" in mime or name.endswith((".mp4", ".mkv", ".webm", ".mov")):
                breakdown["videos"] += size
            elif "pdf" in mime or "word" in mime or name.endswith((".pdf", ".doc", ".docx", ".txt")):
                breakdown["documents"] += size
            elif "audio" in mime or name.endswith((".mp3", ".wav", ".aac")):
                breakdown["audio"] += size
            elif "zip" in mime or name.endswith((".zip", ".tar", ".gz", ".rar", ".7z")):
                breakdown["archives"] += size
            else:
                breakdown["others"] += size
        user = await UserDirectory.get_by_id(owner_id)
        limit = user.get("storage_limit", 15 * 1024 * 1024 * 1024) if user else 15 * 1024 * 1024 * 1024
        return {"total_used_bytes": total_used, "limit_bytes": limit, "percentage_used": round((total_used / limit) * 100, 2), "breakdown_bytes": breakdown}
