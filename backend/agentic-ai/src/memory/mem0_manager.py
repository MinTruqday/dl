from loguru import logger
from typing import List, Dict
import os
from src.core.config import settings


try:
    from mem0 import Memory
    HAS_MEM0 = True
except ImportError:
    HAS_MEM0 = False

class Mem0Manager:
    def __init__(self):
        self.memory = None
        if HAS_MEM0:
            try:
                config = {
                    "vector_store": {
                        "provider": "qdrant",
                        "config": {
                            "host": settings.QDRANT_HOST,
                            "port": settings.QDRANT_PORT,
                            "collection_name": "mem0_memory"
                        }
                    },
                    "llm": {
                        "provider": "litellm",
                        "config": {
                            "model": f"huggingface/{settings.LLAMA_MODEL}",
                            "temperature": 0,
                            "api_key": settings.HF_TOKEN
                        }
                    },
                    "embedder": {
                        "provider": "huggingface",
                        "config": {
                            "model": settings.EMBEDDING_MODEL
                        }
                    }
                }
                self.memory = Memory.from_config(config_dict=config)
                logger.info("Mem0 initialized successfully for long-term memory.")
            except Exception as e:
                logger.error(f"Failed to initialize Mem0: {e}")

    async def add_memory(self, messages: List[Dict], user_id: str):
        if not self.memory or not user_id or user_id == "guess_user":
            return
        try:
            import asyncio
            await asyncio.to_thread(self.memory.add, messages, user_id=user_id)
            logger.info(f"Mem0: Added memory for user {user_id}")
        except Exception as e:
            logger.error(f"Mem0 add_memory error: {e}")

    async def update_memory(self, memory_id: str, new_content: str):
        if not self.memory:
            return
        try:
            import asyncio
            await asyncio.to_thread(self.memory.update, memory_id=memory_id, data=new_content)
            logger.info(f"Mem0: Updated memory {memory_id}")
        except Exception as e:
            logger.error(f"Mem0 update_memory error: {e}")

    async def delete_memory(self, memory_id: str):
        if not self.memory:
            return
        try:
            import asyncio
            await asyncio.to_thread(self.memory.delete, memory_id=memory_id)
            logger.info(f"Mem0: Deleted memory {memory_id}")
        except Exception as e:
            logger.error(f"Mem0 delete_memory error: {e}")

    async def search_and_resolve_conflicts(self, new_content: str, user_id: str):
        if not self.memory or not user_id or user_id == "guess_user":
            return
        try:
            import asyncio
            results = await asyncio.to_thread(self.memory.search, query=new_content, user_id=user_id, limit=5)
            if not results:
                return
            for r in results:
                if r.get("score", 0) > 0.85 and r.get("memory", "") != new_content:
                    await self.delete_memory(r["id"])
                    logger.info(f"Mem0: Resolved conflict - deleted stale memory {r['id']}")
        except Exception as e:
            logger.error(f"Mem0 conflict resolution error: {e}")

    async def get_context(self, query: str, user_id: str) -> str:
        if not self.memory or not user_id or user_id == "guess_user":
            return ""
        try:
            import asyncio
            results = await asyncio.to_thread(self.memory.search, query=query, user_id=user_id)
            if not results:
                return ""
            
            memories = [r["memory"] for r in results if r.get("score", 0) > 0.65]
            if not memories:
                return ""
                
            context = "Thông tin cá nhân hoá của người dùng:\n"
            for i, m in enumerate(memories):
                context += f"- {m}\n"
            return context
        except Exception as e:
            logger.error(f"Mem0 get_context error: {e}")
            return ""

mem0_manager = Mem0Manager()
