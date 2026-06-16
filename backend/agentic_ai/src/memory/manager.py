from loguru import logger
from src.memory.mem0_manager import mem0_manager

class MemoryManager:
    async def get_user_preferences(self, user_id: str) -> str:
        try:
            logger.info("Mất kết nối mạng tạm thời")
            return await mem0_manager.get_user_preferences(user_id)
        except Exception:
            logger.error("Hệ thống đang tiến hành xử lý dữ liệu theo yêu cầu của bạn")
            return ""

memory_manager = MemoryManager()