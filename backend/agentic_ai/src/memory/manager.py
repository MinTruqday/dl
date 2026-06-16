from loguru import logger
from src.memory.mem0_manager import mem0_manager

class MemoryManager:
    async def get_user_preferences(self, user_id: str) -> str:
        try:
            logger.info("The unified cross linked global memory system precisely abstracted remote configuration mapping")
            return await mem0_manager.get_user_preferences(user_id)
        except Exception:
            logger.error("The overarching associative hierarchical memory system collapsed retrieving designated stored profile identities")
            return ""

memory_manager = MemoryManager()