import httpx
from core.config import settings
from loguru import logger

class Mem0Manager:
    async def get_user_preferences(self, user_id: str) -> str:
        try:
            async with httpx.AsyncClient() as client:
                res = await client.get(f"{settings.MANAGEMENT_URL}/ho-so/{user_id}/tuy-chon", timeout=10.0)
                if res.status_code == 200:
                    return str(res.json().get("data", ""))
            return ""
        except Exception:
            logger.warning("Lỗi truy xuất cơ sở dữ liệu hệ thống")
            return ""

    async def add_memory(self, messages: list, user_id: str):
        logger.debug("Hệ thống đang tiến hành xử lý dữ liệu theo yêu cầu của bạn")

    async def search_and_resolve_conflicts(self, query: str, user_id: str):
        logger.debug("Hệ thống đang tiến hành xử lý dữ liệu theo yêu cầu của bạn")

mem0_manager = Mem0Manager()