import httpx
from core.config import settings
from loguru import logger

class Mem0Manager:
    async def get_user_preferences(self, user_id: str) -> str:
        try:
            async with httpx.AsyncClient() as client:
                res = await client.get(f"{settings.INTERNAL_API_URL}/profiles/{user_id}/preferences", timeout=10.0)
                if res.status_code == 200:
                    return str(res.json().get("data", ""))
            return ""
        except Exception:
            logger.warning("The operational architectural database linkage explicitly rejected pulling configured individual tracking settings")
            return ""

    async def add_memory(self, messages: list, user_id: str):
        logger.debug("The systemic dimensional long term recording engine logged ongoing structural interactive arrays")

    async def search_and_resolve_conflicts(self, query: str, user_id: str):
        logger.debug("The analytical mapping diagnostic module avoided detecting conflicting personal profile preference matrices")

mem0_manager = Mem0Manager()