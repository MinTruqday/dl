import os
from loguru import logger
from typing import List, Dict
try:
    from mem0 import Memory
    HAS_MEM0 = True
except ImportError:
    HAS_MEM0 = False
class MemoryAgent:
    def __init__(self):
        self.memory = None
        if HAS_MEM0:
            try:
                config = {
                    "vector_store": {
                        "provider": "qdrant",
                        "config": {
                            "host": os.environ.get("QDRANT_HOST"),
                            "port": int(os.environ.get("QDRANT_PORT")),
                            "collection_name": "mem0_memory"
                        }
                    }
                }
                self.memory = Memory()
                logger.info("Mem0 initialized successfully for long-term usermemory.")
            except Exception as e:
                logger.error(f"Failed to initialize Mem0: {e}")
    def add_memory(self, messages: List[Dict], user_id: str):
        if not self.memory or not user_id or user_id == "guess_user":
            return
        try:
            self.memory.add(messages, user_id=user_id)
            logger.info(f"Added memory to Mem0 for user{user_id}")
        except Exception as e:
            logger.error(f"Mem0 add_memory error: {e}")
    def get_context(self, query: str, user_id: str) -> str:
        if not self.memory or not user_id or user_id == "guess_user":
            return ""
        try:
            results = self.memory.search(query=query, user_id=user_id)
            if not results:
                return ""
            memories = [r["memory"] for r in results if r.get("score", 0) > 0.3]
            if not memories:
                return ""
            context = "Thông tin cá nhân hoá của người dùng (từ trí nhớ ngắn/dài hạn):\n"
            for i, m in enumerate(memories):
                context += f"- {m}\n"
            return context
        except Exception as e:
            logger.error(f"Mem0 get_context error: {e}")
            return ""
memory_agent = MemoryAgent()
